import logging
import os
from threading import Lock, Thread
from datetime import datetime, timedelta
from time import sleep, mktime
from decimal import Decimal
from types import NoneType

from cumin.formats import fmt_datetime, fmt_dict, fmt_none_brief, fmt_none,\
    fmt_duration
from cumin.util import calc_rate, JobStatusInfo, secs, xml_escape
from cumin.sqladapter import SqlAdapter
from rosemary.sqlfilter import SqlComparisonFilter
from rosemary.sqlquery import SqlQueryOptions
from rosemary.model import RosemaryModel
from sage.util import SyncSet

log = logging.getLogger("cumin.model")

class CuminModel(RosemaryModel):
    def __init__(self, app, model_dir):
        super(CuminModel, self).__init__()

        self.app = app
        self.model_dir = model_dir

        self.tasks = list()

        self.limits_by_negotiator = dict()
        self.job_summaries_by_submission = dict()
        self.group_names_by_negotiator = dict()
        
        self.static_group_config_values_by_negotiator = dict()
        self.dynamic_group_config_values_by_negotiator = dict()

        self.lock = Lock()

        self.job_meta_data = JobMetaData("job")

    def check(self):
        log.info("Checking %s", self)

        if not type(self.model_dir) in (list, tuple):
            self.model_dir = [self.model_dir]

        for dirs in self.model_dir:
            assert os.path.isdir(dirs)
            log.debug("Model dir exists at '%s'", dirs)

    def init(self):
        log.info("Initializing %s", self)

        self.load_model_dir(self.model_dir)

        super(CuminModel, self).init()

    def get_ad_groups(self):
        return AdProperty.get_ad_groups()

    def get_class_by_rosemary_object(self, rosemary_object):
        for cls in self.classes:
            if cls.cumin_name.lower() == rosemary_object._class._name.lower():
                return cls

    def get_class_by_object(self, mint_object):
        for cls in self.classes:
            if cls.mint_class is mint_object.__class__:
                return cls

    def show_main(self, session):
        return self.app.main_page.main.show(session)

    def get_session_by_object(self, obj):
        agent = self.app.session.get_agent(obj._qmf_agent_id)
        broker = agent.getBroker()
        session = broker.getAmqpSession()

        return session

    def get_negotiator_group_names(self, negotiator):
        if not negotiator:
            store = NegotiatorGroupNamesStore(self, None)
            store.exception = Exception("Missing Negotiator")
            return store

        self.lock.acquire()

        try:
            try:
                store = self.group_names_by_negotiator[negotiator._qmf_agent_id]
                store.extend_updates()
            except KeyError:
                store = NegotiatorGroupNamesStore(self, negotiator)
                store.start_updates()

                self.group_names_by_negotiator[negotiator._qmf_agent_id] = store

            return store
        finally:
            self.lock.release()

    def get_negotiator_config_values(self, negotiator, needed_groups, config):
        if not negotiator:
            dynamic_store = NegotiatorDynamicGroupConfigValuesStore(self, None)
            dynamic_store.exception = Exception("Missing Negotiator")
            static_store = NegotiatorStaticGroupConfigValuesStore(self, None)
            static_store.exception = Exception("Missing Negotiator")
            return (dynamic_store, static_store)

        self.lock.acquire()
        dynamic_store = None
        static_store = None
        try:
            if config == "GROUP_QUOTA_DYNAMIC":
                try:
                    dynamic_store = self.dynamic_group_config_values_by_negotiator[negotiator._qmf_agent_id]
                    dynamic_store.extend_updates()
                    added = 0
                    for group in needed_groups:
                        added += dynamic_store.add_group_config(group, config)
                    if added > 0:
                        dynamic_store.update_new(None)
                except KeyError:
                    dynamic_store = NegotiatorDynamicGroupConfigValuesStore(self, negotiator, needed_groups, config)
                    dynamic_store.start_updates() 
                    self.dynamic_group_config_values_by_negotiator[negotiator._qmf_agent_id] = dynamic_store                    
                if(negotiator._qmf_agent_id in self.static_group_config_values_by_negotiator.keys()):
                    static_store = self.static_group_config_values_by_negotiator[negotiator._qmf_agent_id]
            else:

                try:
                    static_store = self.static_group_config_values_by_negotiator[negotiator._qmf_agent_id]
                    static_store.extend_updates()
                    added = 0
                    for group in needed_groups:
                        added += static_store.add_group_config(group, config)
                    if added > 0:
                        static_store.update_new(None)
                except KeyError:
                    static_store = NegotiatorStaticGroupConfigValuesStore(self, negotiator, needed_groups, config)
                    static_store.start_updates()
                    self.static_group_config_values_by_negotiator[negotiator._qmf_agent_id] = static_store
                if(negotiator._qmf_agent_id in self.dynamic_group_config_values_by_negotiator.keys()):
                    dynamic_store = self.dynamic_group_config_values_by_negotiator[negotiator._qmf_agent_id]

            return (dynamic_store, static_store)
        finally:
            self.lock.release()

    def update_negotiator_config_value(self, negotiator):
        if not negotiator:
            return

        self.lock.acquire()

        try:
            store = self.dynamic_group_config_values_by_negotiator[negotiator._qmf_agent_id]
            store.update(None)
        finally:
            self.lock.release()

    def get_negotiator_limits(self, negotiator):
        if not negotiator:
            store = NegotiatorLimitStore(self, None)
            store.exception = Exception("Missing Negotiator")
            return store

        self.lock.acquire()

        try:
            try:
                store = self.limits_by_negotiator[negotiator._qmf_agent_id]
                store.extend_updates()
            except KeyError:
                store = NegotiatorLimitStore(self, negotiator)
                store.start_updates()

                self.limits_by_negotiator[negotiator._qmf_agent_id] = store

            return store
        finally:
            self.lock.release()

    def get_submission_job_summaries(self, submission, machine_name=""):
        if not submission:
            store = SubmissionJobSummaryStore(self, None)
            store.exception = Exception("Missing Submission")
            return store

        self.lock.acquire()

        try:
            try:
                store = self.job_summaries_by_submission[submission._id]
                store.extend_updates()
            except KeyError:
                store = SubmissionJobSummaryStore(self, submission, machine_name)
                store.start_updates()

                self.job_summaries_by_submission[submission._id] = store

            return store
        finally:
            self.lock.release()

    def get_jobserver_from_submission(self, session, submission):
        cls = self.com_redhat_grid.JobServer
        job_server = cls.get_object(session.cursor, _id=submission._jobserverRef_id)
        return job_server

    def get_scheduler_from_jobserver(self, session, job_server):
        cls = self.app.model.com_redhat_grid.Scheduler
        return cls.get_object(session.cursor, _id=job_server._schedulerRef_id)

class CuminProperty(object):
    def __init__(self, cls, name):
        self.model = cls.model
        self.cumin_class = cls

        self.name = name
        self.title = None
        self.category = "general"
        self.summary = False
        self.escape = True
        self.prefix = None

        self.cumin_class.add_property(self)

    def init(self):
        pass

    def get_title(self, session):
        if self.title:
            return self.title
        else:
            return self.name

    def value(self, session, object):
        value = getattr(object, self.name, None)

        if isinstance(value, datetime):
            value = fmt_datetime(value)

        if isinstance(value, dict):
            value = fmt_dict(value, self.prefix)

        return value

class AdProperty(object):
    groups = ["Main", "Command Info", "Job Status Info", "Condor Info", "Dates", "Other"]

    def __init__(self, cls, name):
        # don't call super since we don't want to call add_property
        self.cumin_class = cls

        self.name = name
        self.title = None
        self.category = "general"
        self.summary = False
        self.escape = True
        self.prefix = None

        self.description = None
        self.example = None
        self.group = "Main"
        self.renderer = None
        self.writable = True

        self.cumin_class.add_ad_property(self)

    def get_title(self, session):
        if self.title:
            return self.title
        else:
            return self.name

    def value(self, session, object):
        value = getattr(object, self.name, None)

        if isinstance(value, datetime):
            value = fmt_datetime(value)

        if isinstance(value, dict):
            value = fmt_dict(value, self.prefix)

        return value

    @classmethod
    def get_ad_groups(cls):
        return cls.groups

class DictAdProperty(AdProperty):
    def __init__(self, cls, name):
        super(DictAdProperty, self).__init__(cls, name)

        self.renderer = self.render_dict
        self.group = "Other"

    def render_dict(self, session, value):
        return fmt_dict(value, self.prefix)

class DateAdProperty(AdProperty):
    def __init__(self, cls, name):
        super(DateAdProperty, self).__init__(cls, name)

        self.renderer = self.render_datetime
        self.group = "Other"

    def render_datetime(self, session, value):
        #if the timestamp passed in is zero or negative, we translate that to
        # "NA" to display per BZ 696619
        timestamp = value        
        retval = "NA"
        if int(timestamp) > 0:
            value = datetime.fromtimestamp(int(value))
            retval = fmt_datetime(value)            
         
        return retval

class SamplesSqlAdapter(SqlAdapter):
    def __init__(self, app, cls, sig, session, extra_filters=None):
        super(SamplesSqlAdapter, self).__init__(app, cls.sql_samples_table)

        filters = cls.get_sample_filters_by_signature(sig, 
                                         self.app.database.get_read_cursor)
        for f in filters:
            self.query.add_filter(f)
        
        if extra_filters is not None:
            for ef in extra_filters:
                self.query.add_filter(ef)

        self.update_col = cls.get_timestamp_col()
        
        self.session = session        

    def get_sql_options(self, options):
        return options

    def avg_samples(self, stat, secs, interval, secs2):
        stat_col = self.table._columns_by_name[stat.name]
        updated_col = self.table._columns_by_name[self.update_col]

        org_filters = list(self.query.filters)
        max_col = "max(%s) as interval_end" % updated_col.identifier
        value_col = "cast(avg(%s) as integer) as value" % stat_col.identifier
        dev_col = "stddev(%s) as dev" % stat_col.identifier

        columns = list()
        columns.append(max_col)
        columns.append(value_col)
        columns.append(dev_col)
        self.columns = columns

        when = "now() - interval '%i seconds'" % int(secs + secs2)
        filter = SqlComparisonFilter(updated_col, when, ">=")
        self.query.add_filter(filter)
        when2 = ""
        filter2 = None
        if secs2:
            when2 = "now() - interval '%i seconds'" % int(secs2)
            filter2 = SqlComparisonFilter(updated_col, when2, "<=")
            self.query.add_filter(filter2)

        options = SqlQueryOptions()
        options.sort_column = "interval_end"
        options.sort_ascending = False
        options.group_column = "floor(extract(epoch from %s) / %i)" % (updated_col.identifier, interval)

        samples = self.get_data({}, options)

        # reset the filters in case we need to re-run the query in this same request
        del self.query.filters[:]
        self.query.filters = org_filters
        
        #Too many samples will result in a horribly cluttered chart, lets max_samples (parameter)
        max_samples = self.session.get("maxsamp")
        
        reduced_samples = None        
        if max_samples is not None and max_samples > 0 and len(samples) > max_samples:
            reduced_interval = int(len(samples) / max_samples)
            # show every N samples + we always want the first and last
            reduced_samples = [sample for i, sample in enumerate(samples) if i % reduced_interval == 0 or i == 0 or i == len(samples) -1]
            samples = reduced_samples

        return samples

    def samples(self, stat, secs, interval, method, secs2=0, delta=False):
        if method == "avg":
            return self.avg_samples(stat, secs, interval, secs2)

        org_filters = list(self.query.filters)
        stat_col = self.table._columns_by_name[stat.name]
        updated_col = self.table._columns_by_name[self.update_col]

        columns = list()
        columns.append(updated_col.identifier)
        columns.append(stat_col.identifier)
        self.columns = columns

        if not delta:
            when = "now() - interval '%i seconds'" % int(secs + secs2)
            filter = SqlComparisonFilter(updated_col, when, ">=")
            self.query.add_filter(filter)
        when2 = ""
        if secs2:
            when2 = "now() - interval '%i seconds'" % int(secs2)
            filter = SqlComparisonFilter(updated_col, when2, "<=")
            self.query.add_filter(filter)


        options = SqlQueryOptions()
        options.sort_column = updated_col
        options.sort_ascending = False
        if delta:
            options.limit = 2

        samples = self.get_data({}, options)

        # restore the filters
        del self.query.filters[:]
        self.query.filters = org_filters

        return samples

    def recent(self):
        updated_col = self.table._columns_by_name[self.update_col]

        columns = list()
        columns.append(updated_col.identifier)
        self.columns = columns

        options = SqlQueryOptions()
        options.sort_column = updated_col
        options.sort_ascending = False

        samples = self.get_data({}, options)
        return len(samples) and samples[0][0] or None

class CuminStatistic(object):
    formatters = {
        NoneType: lambda x: fmt_none(),
        float: lambda x: "%0.2f" % x,
        Decimal: lambda x: str(x),
        int: lambda x: "%i" % x
        }

    def __init__(self, name):
        self.name = name

    def get_title(self, session):
        return self.name

    def format_value(self, session, value, escape=False):
        return CuminStatistic.fmt_value(value, escape)

    @classmethod
    def fmt_value(cls, value, escape=False):
        try:
            # Don't want to escape the None case because
            # the formatter produces xml, and we don't
            # need to escape the number cases either.
            return cls.formatters[type(value)](value)
        except KeyError:
            # But we do optionally want to escape the string cases
            if escape:
                return xml_escape(value)
            return value

class MetaData(object):
    def __init__(self, name):

        self.name = name
        self.ad_properties = list()
        self.ad_properties_by_name = dict()

    def init(self):
        for ad_prop in self.ad_properties:
            ad_prop.init()

    def add_ad_property(self, prop):
        self.ad_properties.append(prop)
        self.ad_properties_by_name[prop.name] = prop

# XXX "do_" on this doesn't make sense
def do_bind(session, queue_name, binding_info):
        for exchange in binding_info:
            if "key" in binding_info[exchange]:
                binding_key = binding_info[exchange]["key"]
            else:
                binding_key = None

            session.exchange_bind(queue=queue_name,
                exchange=binding_info[exchange]["name"],
                binding_key=binding_key,
                arguments=binding_info[exchange]["arguments"])

class JobMetaData(MetaData):
    def __init__(self, name):
        super(JobMetaData, self).__init__(name)

        ### Main Group
        prop = AdProperty(self, "Owner")
        prop.group = "Main"
        prop.description = "The submitter of the job"
        prop.writable = False

        prop = AdProperty(self, "GlobalJobId")
        prop.group = "Main"
        prop.description = "Unique job id"
        prop.writable = False

        prop = AdProperty(self, "Submission")
        prop.group = "Main"
        prop.description = "Submission name"
        prop.writable = False

        prop = self.JobUniverse(self, "JobUniverse")
        prop.group = "Main"
        prop.title = "Job Universe"
        prop.writable = False
        prop.renderer = prop.render_universe
        
        prop = DateAdProperty(self, "JobStartDate")
        prop.group = "Main"
        prop.writable = False

        ### Condor Info Group
        prop = AdProperty(self, "CondorVersion")
        prop.group = "Condor Info"
        prop.writable = False

        prop = AdProperty(self, "CondorPlatform")
        prop.group = "Condor Info"
        prop.writable = False

        ### Command Info Group
        prop = AdProperty(self, "Args")
        prop.description = "Arguments passed to job Cmd"
        prop.group = "Command Info"

        prop = AdProperty(self, "Cmd")
        prop.description = "Command that will run the job"
        prop.group = "Command Info"

        prop = AdProperty(self, "In")
        prop.description = "The file where the job's standard input is read"
        prop.group = "Command Info"

        prop = AdProperty(self, "Out")
        prop.description = "The file where the job's standard output is written"
        prop.example = "'/dev/null' or '~/logs/'"
        prop.group = "Command Info"

        prop = AdProperty(self, "Err")
        prop.description = "The file where the job's errors are written"
        prop.group = "Command Info"

        prop = AdProperty(self, "Iwd")
        prop.description = "Command Input Working Directory"
        prop.group = "Command Info"
        prop.title = "Working Directory"

        prop = AdProperty(self, "UserLog")
        prop.description = "Log file"
        prop.group = "Command Info"

        ######## Job Status Info
        prop = self.JobStatusProperty(self, "JobStatus")
        prop.description = "The current job status"
        prop.group = "Job Status Info"
        prop.renderer = prop.render_status
        prop.title = "Job Status"
        prop.writable = False

        prop = AdProperty(self, "HoldReasonCode")
        prop.group = "Job Status Info"
        prop.title = "Hold Reason Code"
        prop.writable = False

        prop = self.JobStatusProperty(self, "ExitStatus")
        prop.description = "Status when job completes"
        prop.group = "Job Status Info"
        prop.renderer = prop.render_status
        prop.title = "Exit Status"
        prop.writable = False

        prop = self.JobStatusProperty(self, "LastJobStatus")
        prop.description = ""
        prop.group = "Job Status Info"
        prop.renderer = prop.render_status
        prop.writable = False

        ######## Other
        prop = AdProperty(self, "ProcId")
        prop.description = "The id of the job within its cluster. Proc Ids are unique within a cluster."
        prop.group = "Other"
        prop.title = "Proc Id"
        prop.writable = False

        prop = AdProperty(self, "BufferBlockSize")
        prop.example = "32768"
        prop.group = "Other"

        prop = AdProperty(self, "ClusterId")
        prop.description = "The id of the cluster the job belongs to"
        prop.group = "Other"
        prop.title = "Cluster ID"
        prop.writable = False
        
        prop = AdProperty(self, "CurrentTime")
        prop.group = "Other"
        prop.writable = False

        ###### Dates
        prop = DateAdProperty(self, "QDate")
        prop.description = "When the job was submitted"
        prop.group = "Dates"
        prop.writable = False
              
        #these properties are undecorated unwritable properties
        unwritableProps = ("LastVacateTime", "JobCurrentStartDate", "JobLastStartDate",
                           "LastSuspensionTime", "ShadowBday", "LastJobLeaseRenewal", "EnteredCurrentStatus",
                           "CommittedTime", "LastMatchTime", "ScheddBday", "LastRejMatchTime")

        for currentProp in unwritableProps:
            prop = DateAdProperty(self, currentProp)
            prop.group = "Dates"
            prop.writable = False
 
        # other
        #all of these properties are unwritable and require no description
        unwritableProps = ("User", "MinHosts", "RemoteUserCpu", "DiskUsage", "ImageSize", "RequestMemory",
                           "RequestDisk", "NumShadowStarts", "NumJobStarts", "AutoClusterId",
                           "NumJobMatches", "DiskUsage_RAW", "JobRunCount", "RemoteSlotID",
                           "OrigMaxHosts", "TransferFiles", "RemoteSysCpu", "ImageSize_RAW",
                           "CurrentHosts", "ClaimId", "PublicClaimId", "StartdIpAddr", "StartdPrincipal",
                           "RemoteHost", "NumShadowExceptions", "LastRemoteHost", "LastPuclicClaimId",
                           "BytesRecvd", "RemoteWallClockTime", "BytesSent", "CumulativeSlotTime")
        
        
        for currentProp in unwritableProps:
            prop = AdProperty(self, currentProp)
            prop.group = "Other"
            prop.writable = False
        
      
        prop = AdProperty(self, "RequestMemory")
        prop.description = "Required for scheduling to partitionable slots."
        prop.group = "Other"

        prop = AdProperty(self, "RequestDisk")
        prop.description = "Required for scheduling to partitionable slots."
        prop.group = "Other"
        
    class JobStatusProperty(AdProperty):
        def render_status(self, session, status):
            return JobStatusInfo.get_status_string(status)

    class JobUniverse(AdProperty):
        universes = {None: "Default",
                    5: "Vanilla",
                    7: "Scheduler",
                    9: "Grid",
                    10: "Java",
                    11: "Parallel",
                    12: "Local",
                    13: "VM"}

        def render_universe(self, session, value):
            try:
                # might have a string version of universe
                # value passed in here...
                return self.universes[int(value)]
            except KeyError:
                return "Unknown (%s)" % str(value)

class FetchRawConfigSet(object):
    def __init__(self, timeout=5):
        self.syncs = SyncSet(log, timeout)

    def execute(self, remote, negotiator, groups, prepend=""):
        default = {'Value': 0}
        for group in groups:
            sync = self.syncs.add_sync(group, default, 
                                       remote.get_raw_config.__name__)
            try:
                remote.get_raw_config(negotiator, prepend+group, sync.get_completion())
            except Exception, e:
                sync.error = e
                log.debug("Fetch raw config failed", exc_info=True)
        return self.syncs.do_wait()

class Pool(object):
    def __init__(self, id):
        self.id = id

    def get_collector(self):
        return None

    def get_grid(self):
        return None

    def get_negotiator(self):
        return None

class ObjectStore(object):
    def __init__(self, model):
        self.model = model
        self.data = None
        self.status = None
        self.exception = None

        self.update_thread = self.UpdateThread(self)

    def start_updates(self):
        self.update_thread.start()

    def extend_updates(self):
        self.update_thread.extend()

    def update(self):
        pass

    def delete(self):
        self.model = None

    class UpdateThread(Thread):
        def __init__(self, store):
            Thread.__init__(self)

            self.store = store
            self.setDaemon(True)
            self.ticks = 0

        def extend(self):
            # if we get a request for this object's info
            # keep polling for another 10 minutes
            self.ticks = 0

        def run(self):
            conn = self.store.model.app.database.get_connection()
            cursor = conn.cursor()

            try:
                while self.ticks < 20:
                    try:
                        self.store.update(cursor)
                        self.store.exception = None
                    except Exception, e:
                        log.debug("Object store update failed", exc_info=True)
                        self.store.exception = e

                    self.ticks += 1
                    sleep(30)
            finally:
                conn.close()

            self.store.delete()

class UpdateTimedOut(Exception):
    pass

class NegotiatorLimitStore(ObjectStore):
    def __init__(self, model, negotiator):
        super(NegotiatorLimitStore, self).__init__(model)

        self.negotiator = negotiator

    def update(self, cursor):
        def completion(status, data):
            self.status = status
            try:
                self.data = data["Limits"]
                #self.data =  {'a':{'CURRENT': 11, 'MAX': 22},
                #         'b':{'CURRENT': 3, 'MAX': 44}}
            except KeyError:
                pass

        self.model.app.remote.get_limits(self.negotiator, completion)

    def delete(self):
        del self.model.limits_by_negotiator[self.negotiator._qmf_agent_id]

        super(NegotiatorLimitStore, self).delete()

class SubmissionJobSummaryStore(ObjectStore):
    def __init__(self, model, submission, machine_name=""):
        super(SubmissionJobSummaryStore, self).__init__(model)

        self.submission = submission
        self.machine_name = machine_name

    def update(self, cursor):
        def completion(status, data):
            self.status = status
            try:
                if data is not None:
                    self.data = data["Jobs"]
            except KeyError:
                pass

        self.model.app.remote.get_job_summaries(self.submission, 
                                                completion, 
                                                self.machine_name)

    def delete(self):
        del self.model.job_summaries_by_submission[self.submission._id]

        super(SubmissionJobSummaryStore, self).delete()

    def check_submission_membership(self, job_id):

        # Make sure that the job belongs to the designated submission.
        okay = None
        if self.data is not None:
            okay = False
            for summary in self.data:
                if str(summary["ClusterId"]) + "." + \
                   str(summary["ProcId"]) == job_id:
                    okay = True
                    break
        return okay

class NegotiatorGroupNamesStore(ObjectStore):
    def __init__(self, model, negotiator):
        super(NegotiatorGroupNamesStore, self).__init__(model)

        self.negotiator = negotiator

    def update(self, cursor):
        def completion(status, data):
            self.status = status
            try:
                self.data = data["Value"]
                #self.data = "MSG, GRID, MGMT, RT, GRID.SUB_1, GRID.SUB_1.SUB_A"
            except KeyError:
                pass

        self.model.app.remote.get_raw_config(self.negotiator, "GROUP_NAMES", 
                                             completion)
            
    def delete(self):
        del self.model.group_names_by_negotiator[self.negotiator._qmf_agent_id]

        super(NegotiatorGroupNamesStore, self).delete()

class NegotiatorGroupConfigValuesStore(ObjectStore):
    def __init__(self, model, negotiator, groups, config):
        super(NegotiatorGroupConfigValuesStore, self).__init__(model)

        self.negotiator = negotiator
        self.configs = dict()

        self.configs[config] = list(groups)
        self.data = dict()

    def add_group_config(self, group, config):
        added = 0

        try:
            groups = self.configs[config]
            if not group in groups:
                groups.append(group)
                added = 1
        except KeyError:
            self.configs[config] = [group]
            added = 1

        return added

    def update(self, cursor):
        for config in self.configs:
            action = FetchRawConfigSet()
            raw_configs = action.execute(self.model.app.remote,
                                         self.negotiator, 
                                         self.configs[config], config+"_")
            #for group in raw_configs:
            #    qmfc = raw_configs[group]
            #    qmfc.data = {'Value': 0.1}
            #    qmfc.error = None
            #    qmfc.got_data = True
            #    qmfc.status = "OK"
            self.data[config] = raw_configs

    def update_new(self, cursor):
        for config in self.configs:
            action = FetchRawConfigSet()
            new_configs = list()
            for group in self.configs.keys():
                if group not in self.data.keys() or \
                        self.data[config][group].error or \
                        not self.data[config][group].data:
                    new_configs.append(group)

            raw_configs = action.execute(self.model.app.remote,
                                        self.negotiator, new_configs, config+"_")
            for group in raw_configs:
                self.data[config][group] = raw_configs[group]

    def delete(self):
        try:
            del self.model.static_group_config_values_by_negotiator[self.negotiator._qmf_agent_id]
            del self.model.dynamic_group_config_values_by_negotiator[self.negotiator._qmf_agent_id]
        except KeyError:
            pass        

        super(NegotiatorGroupConfigValuesStore, self).delete()

class NegotiatorDynamicGroupConfigValuesStore(NegotiatorGroupConfigValuesStore):
    def __init__(self, model, negotiator, groups, config):
        super(NegotiatorDynamicGroupConfigValuesStore, self).__init__(model, negotiator, groups, config)
        
class NegotiatorStaticGroupConfigValuesStore(NegotiatorGroupConfigValuesStore):
    def __init__(self, model, negotiator, groups, config):
        super(NegotiatorStaticGroupConfigValuesStore, self).__init__(model, negotiator, groups, config)        
