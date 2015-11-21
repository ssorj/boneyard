import logging
import os
import sys

from mint import *
from parsley.loggingex import *
from stat import StatFlashPage, FlashFullPage
from wooly import Application, Session, Page
from wooly.pages import ResourcePage
from wooly.parameters import IntegerParameter

from admin import *
from database import *
from model import *
from objectselector import *
from objecttask import *
from server import *
from session import *
from sqladapter import *
from user import *
from util import *
from widgets import *
from authenticator import *
from persona import CuminAuthorizator
from sage.catalog import Catalog
from sage.qmf.qmfoperations import QmfOperations
from sage.wallaby.wallabyoperations import WallabyOperations
from wooly import Session
from cumin.widgets import AboutPage

strings = StringCatalog(__file__)
log = logging.getLogger("cumin")

class Cumin(Application):
    def __init__(self, home, broker_uris, database_dsn,
                 host="localhost", port=45672,
                 server_cert="", server_key="",
                 force_secure_cookies=False,
                 persona="default",
                 authmech=[]):
        super(Cumin, self).__init__()

        self.home = home
        self.authmech = authmech
        # For use behind a proxy, when Cumin does not
        # have ssl enabled but the proxy does.
        self.force_secure_cookies = force_secure_cookies

        # Settings for LDAP authentication
        self.ldap_timeout = None
        self.ldap_tls_cacertdir = ""
        self.ldap_tls_cacertfile = ""

        model_dir = [os.path.join(self.home, x) for x in ("model/admin", "model", "model/plumage")]

        self.model = CuminModel(self, model_dir)
        self.session = CuminSession(self, broker_uris)

        self.database = CuminDatabase(self, database_dsn)
        self.server = CuminServer(self, host, port, server_cert, server_key)
        self.admin = CuminAdmin(self)

        self.add_resource_dir(os.path.join(self.home, "resources-wooly"))
        self.add_resource_dir(os.path.join(self.home, "resources"))
        self.add_resource_dir(os.path.join(self.home, "resources-wooly/plugins"))

        self.modules = list()
        self.modules_by_name = dict()

        # This is an argument to CuminAuthorizator in init()
        self.access_path = None
        self.do_authorize = False

        # Currently turned off in config, but maybe used in the future
        self.auth_proxy = None
        self.auth_create_ondemand = None

        self.tasks = list()

        self.user = None
        self.operator_email = None
        self.update_interval = 10
        self.max_qmf_table_sort = 1000
        
        self.fast_view_attributes = list()
        self.notification_timeout = 180
        self.force_html_doctype = False

        self.form_defaults = self.CuminFormDefaults()

        # Persona value maps to xml definitions handled
        # in persona.py
        self.persona = persona

        self._page_links = list()

        # self.model.sql_logging_enabled = True

        # Space separated list of sasl authentication
        # mechanisms, according to the sasl documentation
        self.sasl_mech_list = None

        # Aviary interface.  If server values are "",
        # Aviary operations for that server type will not be used.
        self.aviary_job_servers = ""
        self.aviary_query_servers = ""
        self.aviary_key = ""
        self.aviary_cert = ""
        self.aviary_root_cert = ""
        self.aviary_domain_verify=True
        self.aviary_locator = ""
        
        # For development use only
        self.aviary_suds_logs = False
        self.aviary_prefer_condor = True

        self.wallaby = None
        self.wallaby_broker = None
        self.wallaby_refresh = 60

    def server_alive(self):
        return self.server.server_alive()

    def check(self):
        log.info("Checking %s", self)

        if not os.path.isdir(self.home):
            msg = "Cumin home '%s' not found or not a directory"
            raise Exception(msg % self.home)

        self.model.check()
        self.database.check()
        
    def _init_persona(self, modules):

        # Determine the view based on which modules are enabled
        if "messaging" in modules:
            if "grid" in modules:
                view = MainView(self, "main")
            else:
                view = MessagingMainView(self, "main")
        else:
            view = GridMainView(self, "main")    
          
        self.main_page = MainPage(self, "index.html", view)
        self.add_page(self.main_page, add_to_link_set=True)
        self.set_default_page(self.main_page)

        self.form_page = CuminFormPage(self, "form.html")
        self.add_page(self.form_page)

        self.add_page(StatFlashPage(self, "chart.json"))
        self.add_page(FlashFullPage(self, "flashpage.html"))

        self.export_page = CuminExportPage(self, "csv")
        self.add_page(self.export_page)
        
        self.about_page = AboutPage(self, "about.html")
        self.add_page(self.about_page)        

        self.resource_page.protected = False

        # Enable the modules that are associated with the
        # persona (from persona.py)
        for name in modules:
            try:
                m = __import__(name, globals())
                m.Module(self, name)
            except ImportError:
                pass
            except Exception, e:
                import traceback
                traceback.print_exc()

    def db_init(self, schema_version_check=True):
        self.model.init()
        self.database.init(schema_version_check)

    def init(self, schema_version_check=True):
        log.info("Initializing %s", self)

        # Do this initialization as late as possible so that
        # the application can set config values.
        self.authenticator = CuminAuthenticator(self)
        self.authorizator = CuminAuthorizator(self, self.access_path, self.do_authorize)
        try:
            self.authorizator.set_persona(self.persona)
        except:
            msg = "Persona is not defined '%s'"
            raise Exception(msg % self.persona)
            
        self.authorize_cb = self.authorizator.authorize
        self.mainpage_cb = self.authorizator.find_mainpage

        # Create RPC interfaces for QMF and aviary.
        # These services have overlapping functionality,
        # so they are wrapped in a sage.Catalog object 
        # which allows both to supply operations.  First
        # service in the list takes precedence for any 
        # given op...
        self.remote = Catalog()
        ops = [QmfOperations("qmf", self.session)]

        imports_ok = True
        if self.aviary_job_servers or self.aviary_query_servers:
            try:
                from sage.aviary.aviaryoperations import \
                    SudsLogging, AviaryOperationsFactory
            except:
                imports_ok = False
            if imports_ok:
                SudsLogging.set(self.aviary_suds_logs, self.home)

                # By default Cumin uses /var/lib/condor/aviary/services for
                # aviary wsdl files if it exists.
                aviary_dir = ["/var/lib/condor/aviary/services",
                              os.path.join(self.home, "rpc-defs/aviary")]
                if not self.aviary_prefer_condor:
                    aviary_dir = [aviary_dir[1], aviary_dir[0]]

                # The factory will choose an impl that gives us jobs, queries,
                # or both depending on whether job_servers and query_servers 
                # are empty strings. If locator is non empty, their actual 
                # values will be overridden but the presence of a value will 
                # still control enable/disable.
                aviary_itf = AviaryOperationsFactory("aviary", aviary_dir,
                                 self.aviary_locator,
                                 self.aviary_job_servers,
                                 self.aviary_query_servers,
                                 key=self.aviary_key, 
                                 cert=self.aviary_cert,
                                 root_cert=self.aviary_root_cert,
                                 domain_verify=self.aviary_domain_verify)
                ops.insert(0, aviary_itf)
            else:
                log.info("Imports failed for Aviary interface, disabling")

        log.info("%s Aviary locator interface" % \
                ((self.aviary_locator and \
                  (self.aviary_job_servers or \
                   self.aviary_query_servers) and \
                  imports_ok) and "Enabled" or "Disabled"))
                
        log.info("%s Aviary interface for job submission and control." % \
                 ((self.aviary_job_servers and imports_ok) and "Enabled" or "Disabled"))

        log.info("%s Aviary interface for query operations." % \
                 ((self.aviary_query_servers and imports_ok) and "Enabled" or "Disabled"))

        self.remote.add_mechanisms(ops)

        # Create RPC interface for Wallaby
        # The Wallaby client API needs a broker connection.  The broker host
        # for Wallaby is not necessarily the same as the broker used by
        # cumin-web for grid data, and flags set on the Session for cumin
        # may not be appropriate for the Wallaby API.  So, it gets its own.
        self.wallaby = WallabyOperations(self.wallaby_broker,
                                         self.wallaby_refresh,
                                         self.sasl_mech_list)
        
        self.model.init()
        self.session.init()
        self.database.init(schema_version_check)
        self.server.init()

        # This will set up the main view and enable the
        # modules that are associated with the persona
        self._init_persona(self.authorizator.get_enabled_modules())

        for module in self.modules:
            module.init()

        for task in self.tasks:
            task.init()

        super(Cumin, self).init()

    def start(self):
        log.info("Starting %s", self)

        self.session.start()
        self.server.start()
        if self.wallaby is not None:
            self.wallaby.start()

    def stop(self):
        log.info("Stopping %s", self)

        if self.wallaby is not None:
            self.wallaby.stop(wait=True)

        self.server.stop()
        try:
            self.session.stop()
        except:
            pass

    def set_form_defaults(self, 
                          request_memory,
                          request_memory_vm,
                          request_disk,
                          request_disk_vm):
        self.form_defaults.request_memory = request_memory
        self.form_defaults.request_memory_vm = request_memory_vm
        self.form_defaults.request_disk = request_disk
        self.form_defaults.request_disk_vm = request_disk_vm

    class CuminFormDefaults(object):
        def __init__(self):
            self.request_memory = 0
            self.request_memory_vm = 0
            self.request_disk = 0
            self.request_disk_vm = 0

class CuminModule(object):
    def __init__(self, app, name):
        self.app = app
        self.name = name
        self.tasks = list()
        log.debug("Init cumin module %s", name )
        assert not hasattr(app, self.name), self.name

        self.app.modules.append(self)
        setattr(self.app, self.name, self)

    def init(self):
        for task in self.tasks:
            task.init()

    def init_test(self, test):
        pass

class GridMainView(CuminMainView):
    def __init__(self, app, name):
        super(GridMainView, self).__init__(app, name)

class MessagingMainView(CuminMainView):
    def __init__(self, app, name):
        super(MessagingMainView, self).__init__(app, name)

        self.overview = MessagingOverviewFrame(app, "overview")
        self.add_tab(self.overview)

class MainView(CuminMainView):
    def __init__(self, app, name):
        super(MainView, self).__init__(app, name)

        self.overview = OverviewFrame(app, "overview")
        self.add_tab(self.overview)

class MainPage(CuminPage, ModeSet):
    def __init__(self, app, name, main_view):
        super(MainPage, self).__init__(app, name)

        self.main = main_view
        self.add_mode(self.main)
        self.set_default_frame(self.main)
        self.cumin_module = ["messaging", "grid"]

        self.page_html_class = "Cumin"

    def render_title(self, session):
        return self.get_title(session)

    def get_title(self, session):
        return "Administrator"

# XXX Add qmf tab

class OverviewFrame(CuminFrame):
    def __init__(self, app, name):
        super(OverviewFrame, self).__init__(app, name)

        self.view = self.get_overview_view(app)
        self.add_mode(self.view)

        self.notice = ConfigurationNotice(app, "notice")
        self.add_mode(self.notice)

    def get_overview_view(self, app):
        return OverviewView(app, "view")

    def do_process(self, session):
        super(OverviewFrame, self).do_process(session)

        configured_count = len([x for x in self.app.session.qmf_brokers if x.host != "localhost"])
        connected_count = len([x for x in self.app.session.qmf_brokers if x.connected])

        # there were no user defined entries in cumin.conf and localhost isn't connected
        if (configured_count == 0) and (connected_count == 0):
            self.mode.set(session, self.notice)

    def render_title(self, session):
        return "Overview"

class OverviewView(Widget):
    def __init__(self, app, name):
        super(OverviewView, self).__init__(app, name)

        queues = TopQueueTable(app, "queues")
        self.add_child(queues)

        systems = TopSystemTable(app, "systems")
        self.add_child(systems)
        systems.cumin_module = "inventory"

        submissions = TopSubmissionTable(app, "submissions")
        self.add_child(submissions)
        submissions.cumin_module = "grid"

class MessagingOverviewFrame(OverviewFrame):
    def __init__(self, app, name):
        super(MessagingOverviewFrame, self).__init__(app, name)

    def get_overview_view(self, app):
        return MessagingOverviewView(app, "view")

class MessagingOverviewView(Widget):
    def __init__(self, app, name):
        super(MessagingOverviewView, self).__init__(app, name)

        queues = TopQueueTable(app, "queues")
        self.add_child(queues)

        systems = TopSystemTable(app, "systems")
        self.add_child(systems)

class ConfigurationNotice(Widget):
    pass

class TopQueueAdapter(SqlAdapter):
    def __init__(self, app, cls):
        super(TopQueueAdapter, self).__init__(app, cls.sql_table)
        self.cls = cls

    def init(self):
        super(TopQueueAdapter, self).init()

        name_col = self.table._columns_by_name["name"]
        avg_over_last_60_seconds_col = """((sum("Queue"."msgTotalEnqueues") - 
            sum(s."msgTotalEnqueues")) / (count(1)-1)) / 300 as avg_60"""
        queue_id_col = self.table._columns_by_name["_id"]
        vhostRef_col = self.table._columns_by_name["_vhostRef_id"]
        vhost_table = self.app.model.org_apache_qpid_broker.Vhost.sql_table
        vhost_id_col = vhost_table._columns_by_name["_id"]
        vhost_brokerRef_col = vhost_table._columns_by_name["_brokerRef_id"]

        self.columns.append(name_col)
        self.columns.append(avg_over_last_60_seconds_col)
        self.columns.append(vhost_brokerRef_col)
        self.columns.append(queue_id_col)

        sub_query = "(%s) as s" % self.get_sub_query_text()
        SqlInnerJoin(self.query, sub_query,
                     queue_id_col, "s._parent_id")

        SqlInnerJoin(self.query, vhost_table,
             vhostRef_col, vhost_id_col)

    def get_sub_query_text(self):
        samples_table = self.cls.sql_samples_table
        subquery = SqlQuery(samples_table)
        parent_col = samples_table._columns_by_name["_parent_id"]
        updated_col = samples_table._columns_by_name["_qmf_update_time"]
        enqueues_col = samples_table._columns_by_name["msgTotalEnqueues"]

        when = "now() - interval '600 seconds'"
        filter = SqlComparisonFilter(updated_col, when, ">=")
        subquery.add_filter(filter)

        columns = list()
        columns.append(parent_col)
        columns.append(enqueues_col)

        return subquery.emit(columns)

    def get_data(self, values, options):
        options.sort_column = "avg_60"
        options.sort_ascending = False

        options.group_column = "%s, %s, %s" % ("\"Queue\".name", "\"Queue\"._id", "\"Vhost\".\"_brokerRef_id\"")
        having = SqlComparisonFilter("count(1)", "1", ">")
        options.group_having.append(having)

        try:
            data = super(TopQueueAdapter, self).get_data(values, options)
        except:
            data = []
        return data

    def get_sql_options(self, options):
        return options

class TopQueueTable(TopTable):
    def __init__(self, app, name):
        cls = app.model.org_apache_qpid_broker.Queue
        super(TopQueueTable, self).__init__(app, name, cls)

        frame = "main.messaging.broker.queue"
        col = self.NameColumn(app, "name", cls.name, cls._id, frame)
        self.add_column(col)

        col = self.add_attribute_column(cls.msgDepth)
        self.set_default_sort_column(col)

    def init(self):
        super(TopQueueTable, self).init()

        self.adapter.vhost_id_field = ObjectSqlField \
            (self.adapter, self.cls.vhostRef)

        filter = SqlComparisonFilter(self.cls.msgDepth.sql_column,
                                     "null",
                                     "is not")
        self.adapter.query.add_filter(filter)

    def render_rows(self, session):
        data = self.data.get(session)

        writer = Writer()

        for record in data:
            # if there is no broker id, don't render the row
            if record[self.adapter.vhost_id_field.index]:
                writer.write(self.row.render(session, record))

        return writer.to_string()

    class NameColumn(ObjectLinkColumn):
        def render_cell_href(self, session, record):
            branch = session.branch()

            frame = self.page.main.messaging.broker
            adapter = self.table.adapter

            frame.id.set(branch, record[adapter.vhost_id_field.index])
            frame.queue.id.set(branch, record[adapter.id_field.index])
            frame.queue.view.show(branch)

            return branch.marshal()

class TopSystemTable(TopTable):
    def __init__(self, app, name):
        cls = app.model.com_redhat_sesame.Sysimage

        super(TopSystemTable, self).__init__(app, name, cls)

        frame = "main.inventory.system"
        col = ObjectLinkColumn(app, "name", cls.nodeName, cls._id, frame)
        self.add_column(col)

        col = self.add_attribute_column(cls.loadAverage1Min)
        self.set_default_sort_column(col)

    def init(self):
        super(TopSystemTable, self).init()

        filter = SqlComparisonFilter(self.cls.loadAverage1Min.sql_column,
                                     "null",
                                     "is not")
        self.adapter.query.add_filter(filter)

class TopSubmissionTable(TopTable):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Submission

        super(TopSubmissionTable, self).__init__(app, name, cls)

        col = self.NameColumn(app, cls.Name.name, cls.Name, cls._id, None)
        self.add_column(col)

#        col = self.DurationColumn(app, cls._qmf_create_time.name,
#                                  cls._qmf_create_time)

        col = self.DurationColumn(app, cls.QDate.name, cls.QDate)
        self.add_column(col)
        self.set_default_sort_column(col)

    def init(self):
        super(TopSubmissionTable, self).init()

        table = self.cls.sql_table

        filter = SqlComparisonFilter(table.Running, "0", ">")
        self.adapter.query.add_filter(filter)

    def render_rows(self, session):
        data = self.data.get(session)

        writer = Writer()

        for record in data:
            # if we can't get the collector, don't render the row
            submission_id = record[0]

            job_server = self.get_job_server(session, submission_id)
            if job_server:
                writer.write(self.row.render(session, record))
        return writer.to_string()

    def get_job_server(self, session, submission_id):
        try:
            submission = self.cls.get_object_by_id(session.cursor, submission_id)
            cls = self.app.model.com_redhat_grid.JobServer
            return cls.get_object_by_id(session.cursor, submission._jobserverRef_id)
        except:
            log.debug("Getting job server failed", exc_info=True)

    class NameColumn(ObjectLinkColumn):
        def render_cell_href(self, session, record):
            submission_id = record[0]

            cls = self.app.model.com_redhat_grid.Collector
            collector = self.app.model.find_youngest(cls, session.cursor)            
            job_server = self.parent.get_job_server(session, submission_id)

            # XXX BZ699413
            # The collector id in the session is referenced by a bunch of
            # classes, so it still needs to exist, even though it is not
            # used for filtering.  Try to remove references to it in another
            # pass.
            if job_server and collector:
                branch = session.branch()
                self.page.main.grid.id.set(session, collector._id)
                self.page.main.grid.submission.id.set(session, submission_id)
                self.page.main.grid.submission.view.show(session)
                return branch.marshal()
            
        def render_cell_content(self, session, record):
            retval = len(record) > 0 and record[self.field.index] or ""
            if(len(record[self.field.index]) > 50):
                retval = record[self.field.index][:50] + "..."  #indicate that we truncated the name
            return retval

    class DurationColumn(TopTableColumn):
        def render_header_content(self, session):
            return "Duration"

        def render_cell_content(self, session, record):
            qdate = self.field.get_content(session, record)
            if qdate is None:
                return 0

            import time
            return fmt_duration(time.time() - secs(qdate))

        def render_text_align(self, session):
            return "right"
