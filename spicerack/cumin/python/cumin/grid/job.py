import logging
import os
from datetime import datetime

from cumin.objectframe import ObjectView, ObjectFrameTaskForm, ObjectFrame,\
    ObjectFrameTask
from cumin.qmfadapter import ObjectQmfAdapter
from cumin.objectselector import ObjectTableColumn, ObjectLinkColumn,\
    ObjectQmfSelectorTable, ObjectCheckboxColumn,\
    ObjectSelectorTask, ObjectSelectorTaskForm, ObjectQmfSelector
from cumin.widgets import StaticColumnHeader, Wait, CuminForm,\
    EditablePropertyRenderer, StateSwitch
from cumin.util import JobStatusInfo, strip_string_quotes, parse
from cumin.formats import fmt_datetime, fmt_link

from wooly import Widget, Parameter, Attribute
from wooly.util import StringCatalog, Writer, escape_amp, escape_entity,\
    xml_escape
from wooly.forms import Form, FormButton, StringField, NoXMLStringField, FormError
from wooly.widgets import ModeSet, PropertySet, TemplateRenderer, Notice
from wooly.template import WidgetTemplate
from wooly.parameters import ListParameter, IntegerParameter, DictParameter

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.job")

class JobFrame(ObjectFrame):
    def __init__(self, app, name, submission, check_viewable=False):
        cls = app.model.com_redhat_grid.Submission

        super(JobFrame, self).__init__(app, name, cls)
        
        self.view = JobView(app, "view", self.object)
        self.replace_child(self.view)
        self.do_check_viewable = check_viewable

        # view or edit
        
        self.ads = JobAdModes(app, "ads", check_viewable)
        self.view.add_tab(self.ads)

        self.view.add_tab(JobOutput(app, "output", check_viewable))

        self.job_id = Parameter(app, "job_id")
        self.add_parameter(self.job_id)

        JobHold(app, self)
        JobRelease(app, self)
        JobSuspend(app, self)
        JobContinue(app, self)
        JobRemove(app, self)

        # task not visible on page. used for edit submit
        self.set_ad_task = JobSetAttribute(app, self)

    def get_title(self, session):
        job_id = self.job_id.get(session)
        return "Job %s" % job_id

    def show_ads_edit(self, session):
        self.ads.editor.show(session)

    def show_ads_view(self, session):
        self.ads.viewer.show(session)

    def get_submission(self, session, id):
        return self.get_object(session, id)

    def get_job_server(self, session, id):
        submission = self.get_submission(session, id)

        cls = self.app.model.com_redhat_grid.JobServer
        return cls.get_object(session.cursor, _id=submission._jobserverRef_id)

    def get_trifecta(self, session, id):
        # return submission, job_server, and scheduler too!
        submission = self.get_submission(session, id)

        cls = self.app.model.com_redhat_grid.JobServer
        js = cls.get_object(session.cursor, _id=submission._jobserverRef_id)
        
        cls = self.app.model.com_redhat_grid.Scheduler
        sched = cls.get_object(session.cursor, _id=js._schedulerRef_id)
        return (submission, js, sched)

    def get_scheduler(self, session, id):
        job_server = self.get_job_server(session, id)

        cls = self.app.model.com_redhat_grid.Scheduler
        return cls.get_object(session.cursor, _id=job_server._schedulerRef_id)

    def get_href(self, session, id, job_id):
        branch = session.branch()

        self.id.set(branch, id)
        self.job_id.set(branch, job_id)
        self.view.show(branch)

        return branch.marshal()

    def not_viewable_redirect(self):
        # The object held by this frame is actually a submission,
        # so a redirect from a higher level should use this message
        return (self.parent, 
                "Logged in user does not own the specified submission")

    def get_job_ad(self, session, id=None, job_id=None):
        if id is None:
            id = self.id.get(session)
        if job_id is None:
            job_id = self.job_id.get(session)
        submission, job_server, sched = self.get_trifecta(session, id)
        results = self.app.remote.get_job_ad(job_server, job_id, 
                                             sched.Name, submission,
                                             default={'JobAd': {}})
        return results

    def check_submission_membership(self, session, sub_id, job_id):
        frame = None
        message = ""
        submission, js, sched = self.get_trifecta(session, sub_id)
        summaries = self.app.model.get_submission_job_summaries(submission, 
                                                                sched.Name)

        # Make sure that the job belongs to the designated submission.
        # None = no data
        # True/False indicates job is a member of the submission
        okay = summaries.check_submission_membership(job_id)

        if okay is None:
            # Well, someone is requesting a particular job but we have no
            # data yet so we don't know if it is legit or not.  Redirect
            # to the parent frame, but without a notice. Normally data should
            # be present because the trail through Cumin goes to the submission
            # job list first, with a link to a particular job.
            frame = self.parent
        elif not okay:
            frame = self.parent
            message = "Job %s is not part "\
                      "of the specified submission" % job_id

        return okay, frame, message

    def do_process(self, session):
        super(JobFrame, self).do_process(session)

        # Make sure that the job belongs to the designated submission.
        sub_id = self.id.get(session)
        job_id = self.job_id.get(session)
        okay, frame, message = self.check_submission_membership(session, 
                                                                sub_id, job_id)
        # If the check failed and there is not yet a redirect
        # value, set the redirect.  Add the notice in either case.
        if not okay:
            if not self.get_redirect(session) and frame:
                self.set_redirect(session, frame, message)
            elif message:
                session.add_notice(Notice(message))

class JobAdModes(ModeSet):
    def __init__(self, app, name, check_viewable):
        super(JobAdModes, self).__init__(app, name)

        self.viewer = JobAdsViewer(app, "viewer")
        self.add_mode(self.viewer)
        self.viewer.do_check_viewable = check_viewable

        self.editor = JobAdsEditor(app, "editor")
        self.add_mode(self.editor)
        self.editor.do_check_viewable = check_viewable

    def render_title(self, session):
        return "Attributes"
    
class JobAdFastView(ModeSet):
    def __init__(self, app, name):
        super(JobAdFastView, self).__init__(app, name)

        self.viewer = FastViewJobAdsViewer(app, "fastviewer")
        self.add_mode(self.viewer)

    def render_title(self, session):
        return "Overview"    

class JobView(ObjectView):
    def add_details_tab(self):
        pass

    def render_title(self, session):
        return self.frame.get_title(session)

class JobSummariesAdapter(ObjectQmfAdapter):
    def __init__(self, app, cls, submission):
        super(JobSummariesAdapter, self).__init__(app, cls)

        self.submission = submission

    def get_qmf_results(self, values):
        session = values['session']
        submission = self.submission.get(session)
        try:
            js = self.app.model.get_jobserver_from_submission(session, 
                                                          submission).Machine
        except:
            js = ""
        return self.app.model.get_submission_job_summaries(submission, js)

    def do_get_data(self, values):
        results = self.get_qmf_results(values)
        summaries = results.data

        if summaries is None or len(summaries) == 0:
            return []

        return summaries

    def process_record(self, key, record):
        field_data = list()
        for column in self.columns:
            try:
                val = record[column.name]
                # translate status int into string so the column can be sorted correctly
                if column.name == "JobStatus":
                    val = JobStatusInfo.get_status_string(val)
            except KeyError:
                val = None
                if column.name == "JobId":
                    # GlobalJobId should look like localhost6.localdomain6#94.1#1284091602
                    # (Coming from Aviary, the qdate won't be present 
                    # (the bit after the last #)
                    try:
                        gjid = record["GlobalJobId"]
                        parts = gjid.split("#")
                        if len(parts) in (2,3):
                            val = parts[1]
                    except Exception:
                        pass
                    if not val:
                        try:
                            val = "%s.%s" % (str(record["ClusterId"]), str(record["ProcId"]))
                        except KeyError:
                            val = "0"
                else:
                    val = 0
            field_data.append(val)
        return field_data

    def get_count(self, values):
        data = self.do_get_data(values)
        return len(data)

class NonSortableObjectTableColumn(ObjectTableColumn):
    def __init__(self, app, name, attr):
        super(NonSortableObjectTableColumn, self).__init__(app, name, attr)

        self.header = StaticColumnHeader(app, "header")
        self.replace_child(self.header)

class DynamicColumnHeader(Widget):
    def __init__(self, app, name, selector_method, col):
        super(DynamicColumnHeader, self).__init__(app, name)

        # save the original sortable header
        self.sortable_header = col.header

        # add a static header
        self.static_header = StaticColumnHeader(app, "static_header")
        col.add_child(self.static_header)

        self.selector_method = selector_method

    def render(self, session):
        render_sortable = self.selector_method(session)

        if render_sortable:
            return self.sortable_header.render(session)
        else:
            return self.static_header.render(session)

class DynamicSortableObjectLinkColumn(ObjectLinkColumn):
    def __init__(self, app, name, attr, id_attr, frame_path, selector_method):
        super(DynamicSortableObjectLinkColumn, self).__init__(app, name, attr, id_attr, frame_path)

        # add an object that selects between the static and sortable header
        self.header = DynamicColumnHeader(app, "dynamic_header", selector_method, self)
        self.add_child(self.header) 

class DynamicSortableObjectTableColumn(ObjectTableColumn):
    def __init__(self, app, name, attr, selector_method):
        super(DynamicSortableObjectTableColumn, self).__init__(app, name, attr)

        self.header = DynamicColumnHeader(app, "dynamic_header", selector_method, self)
        self.add_child(self.header) 

class JobSelector(ObjectQmfSelector):
    def __init__(self, app, name, submission):
        cls = app.model.com_redhat_cumin_grid.JobSummary

        super(JobSelector, self).__init__(app, name, cls)

        self.table.adapter = JobSummariesAdapter(app, cls, submission)

        self.submission = submission
        frame = "main.grid.submission.job"
        self.job_id_col = self.JobIdColumn(app, "job", cls.GlobalJobId, cls.JobId, frame, self.render_dynamic_header)
        self.add_column(self.job_id_col)

        status_column = DynamicSortableObjectTableColumn(app, "status", cls.JobStatus, self.render_dynamic_header)
        self.add_column(status_column)

        cmd_column = NonSortableObjectTableColumn(app, cls.Cmd.name, cls.Cmd)
        self.add_column(cmd_column)

        self.job_id_column = ObjectTableColumn(app, cls.JobId.name, cls.JobId)
        self.job_id_column.visible = False
        self.add_column(self.job_id_column)

        JobSelectionHold(app, self, "held")
        JobSelectionRelease(app, self, "released")
        JobSelectionSuspend(app, self, "suspended")
        JobSelectionContinue(app, self, "continued")
        JobSelectionRemove(app, self, "removed")

        self.enable_csv_export(submission)
        self.add_search_filter(self.job_id_col)

    def create_table(self, app, name, cls):
        return JobSelectorTable(app, name, cls)

    def get_qmf_results(self, session):
        values = self.get_data_values(session)
        return self.table.adapter.get_qmf_results(values)

    def render_dynamic_header(self, session):
        values = self.get_data_values(session)
        count = self.table.adapter.get_count(values)
        max_sort = self.table.adapter.max_sortable_records

        return count <= max_sort

    def render_title(self, session):
        return "Jobs"

    class JobIdColumn(DynamicSortableObjectLinkColumn):
        def render_cell_href(self, session, record):
            if len(record) == 0:
                return ""
            job_id = record[self.parent.parent.job_id_column.field.index]
            #frame = self.page.page_widgets_by_path[self.frame_path]
            frame = self.table.parent.frame.job

            submission = self.parent.parent.submission.get(session)
            return frame.get_href(session, submission._id, job_id)

class JobSelectorTable(ObjectQmfSelectorTable):
    def init_ids(self, app, cls):
        item = Parameter(app, "item")

        self.ids = ListParameter(app, "selection", item)
        self.add_parameter(self.ids)

        self.checkbox_column = ObjectCheckboxColumn \
            (app, "id", cls.JobId, self.ids)
        self.add_column(self.checkbox_column)

    def do_render(self, session):
        # Set redirect if the submission object we depend on is missing
        if self.frame.object.get(session) is None:
            nsession = session.branch()
            frame = self.frame.parent
            frame.view.show(nsession)
            submission_list_url = nsession.marshal()
            self.page.redirect.set(session, submission_list_url)
            session.add_notice(Notice("The submission being displayed became unavailable"))
        else:
            return super(JobSelectorTable, self).do_render(session)

class JobObjectSelectorTask(ObjectSelectorTask):
    def __init__(self, app, selector, verb, cmd):
        super(JobObjectSelectorTask, self).__init__(app, selector)

        self.form = JobObjectSelectorTaskForm(app, self.name, self, verb)
        self.cmd = cmd

    def do_invoke(self, invoc, job_id, scheduler, reason, submission):
        self.app.remote.control_job(self.cmd, scheduler, 
                                    job_id, reason, submission, 
                                    callback=invoc.make_callback())

    def do_enter(self, session, osession):
        submission = self.selector.submission.get(osession)
        self.form.submission_id.set(session, submission._id)

    def get_item_content(self, session, item):
        # item here is the unicode job id
        return xml_escape(item)

class JobSelectionHold(JobObjectSelectorTask):
    def __init__(self, app, selector, verb):
        super(JobSelectionHold, self).__init__(app, selector, verb,
                                               "holdJob")

    def get_title(self, session):
        return "Hold"

class JobSelectionRelease(JobObjectSelectorTask):
    def __init__(self, app, selector, verb):
        super(JobSelectionRelease, self).__init__(app, selector, verb,
                                                  "releaseJob")

    def get_title(self, session):
        return "Release"

class JobSelectionRemove(JobObjectSelectorTask):
    def __init__(self, app, selector, verb):
        super(JobSelectionRemove, self).__init__(app, selector, verb,
                                                 "removeJob")

    def get_title(self, session):
        return "Remove"

class JobSelectionSuspend(JobObjectSelectorTask):
    def __init__(self, app, selector, verb):
        super(JobSelectionSuspend, self).__init__(app, selector, verb,
                                                  "suspendJob")

    def get_title(self, session):
        return "Suspend"

class JobSelectionContinue(JobObjectSelectorTask):
    def __init__(self, app, selector, verb):
        super(JobSelectionContinue, self).__init__(app, selector, verb,
                                                   "continueJob")

    def get_title(self, session):
        return "Continue"

class JobObjectSelectorTaskForm(ObjectSelectorTaskForm):
    def __init__(self, app, name, task, verb):
        super(JobObjectSelectorTaskForm, self).__init__(app, name, task)

        self.submission_id = IntegerParameter(app, "sub")
        self.add_parameter(self.submission_id)

        self.reason = ReasonField(app, "reason")
        self.reason.required = True
        self.main_fields.add_field(self.reason)
        self.add_child(self.reason)

        self.verb = verb

    def get_selection(self, session):
        ids = self.ids.get(session)

        selection = list(ids)
        self.selection.set(session, selection)
        return len(selection)

    def get_reason(self, session, verb):
        """ returns <verb> by username[: <user input reason>] """
        reason = self.reason.get(session)
        if reason:
            reason = [reason]
            user = session.client_session.attributes["login_session"].user

            verb_by = "%s by %s" % (verb, user.name)
            reason.insert(0, verb_by)
            return ": ".join(reason)

    def process_submit(self, session):
        selection = self.selection.get(session)
        submission, scheduler = self.get_submission_sched(session)

        self.validate(session, selection, submission, scheduler)

        errors = self.errors.get(session)
        if not errors:
            reason = self.get_reason(session, self.verb)
            self.task.invoke(session, selection, scheduler, reason, submission)
            self.task.exit_with_redirect(session)

    def get_submission_sched(self, session):
        submission_id = self.submission_id.get(session)
        cls = self.app.model.com_redhat_grid.Submission
        submission = cls.get_object_by_id(session.cursor, submission_id)

        cls = self.app.model.com_redhat_grid.JobServer
        job_server = cls.get_object(session.cursor, _id=submission._jobserverRef_id)

        cls = self.app.model.com_redhat_grid.Scheduler
        sched = cls.get_object(session.cursor, _id=job_server._schedulerRef_id)
        return (submission, sched)

    def render_content(self, session, *args):
        content = super(JobObjectSelectorTaskForm, self).render_content(session, *args)
        reason = self.reason.render(session)
        return "<table class=\"FormFieldSet\"><tbody>%s</tbody></table>%s" % (reason, content)

    def validate(self, session, 
                 selection=None, submission=None, sched=None):
        super(JobObjectSelectorTaskForm, self).validate(session)
        if not self.errors.get(session) and \
               self.app.authorizator.is_enforcing():

            if selection is None:
                selection = self.get_selection(session)
            if submission is None or sched is None:
                submission, sched = self.get_submission_sched(session)

            # Check here to make sure the logged in user owns
            # the submission or is an admin
            login = session.client_session.attributes["login_session"]
            if "admin" not in login.group:
                user = login.user.name
                if hasattr(submission, "Owner") and submission.Owner != user:
                    f = FormError("The logged in user does not "\
                                  "own this submission.")
                    self.errors.add(session, f)

            # Check that the job is a member of the submission
            summaries = self.app.model.get_submission_job_summaries(submission,
                                                                    sched.Name)

            # Make sure that the job belongs to the designated submission.
            # None = no data
            # True/False indicates job is a member of the submission
            for sel in selection:
                okay = summaries.check_submission_membership(sel)
                if okay is None:
                    f = FormError("Unable to verify job %s" \
                                  " is a member of the submission" % sel)
                    self.errors.add(session, f)
                elif not okay:
                    f = FormError("Job %s is not part of" \
                                  " the specified submission" % sel)
                    self.errors.add(session, f)

class JobAdsSet(PropertySet):
    types = {0: "expression",
             1: "integer",
             2: "float",
             3: "string"}

    def __init__(self, app, name):
        super(JobAdsSet, self).__init__(app, name)

        self.items = Attribute(app, "cached_items")
        self.add_attribute(self.items)

        self.qmf_error = Attribute(app, "qmf_error")
        self.add_attribute(self.qmf_error)

        self.do_check_viewable = False

    def get_job_ad(self, session):
        # defer to the frame because it's got all the data
        return self.frame.get_job_ad(session)

    def check_job_owner(self, session, ad):
        error = None
        if not session.client_session.check_owner(ad['Owner']):
            class InventError:
                def __init__(self, msg):
                    self.args = [msg]
            error = InventError("Logged in user does not own the specified job")
        return error

    def do_get_items(self, session):
        ad_list = self.items.get(session)
        error = self.qmf_error.get(session)
        if not ad_list and not error:
            ad_list = list()
            results = self.get_job_ad(session)
            error = None
            if results.error:
                error = results.error    
            elif self.do_check_viewable:
                error = self.check_job_owner(session, results.data['JobAd'])

            self.qmf_error.set(session, error)
            ads = results.data['JobAd']
            cls = self.app.model.job_meta_data
            ad_list = [self.gen_item(x, ads[x], cls, dtype=self.get_type(ads, x)) \
                       for x in ads if not x.startswith("!!")]
            self.items.set(session, ad_list)

        return ad_list, error

    def get_desc(self, descriptors, x):
        if x in descriptors:
            return descriptors[x]
        return ""

    def get_type(self, ads, x):
        value = ads[x]
        if isinstance(value, (int, long)):
            type = "integer"
        elif isinstance(value, float):
            type = "float"
        elif isinstance(value, dict):
            type = "dict"
        else:
            type = "string"
            # This will have to change to support queries from
            # aviary.  The !!descriptors convention is from qmf
            # Probably, a common form for job ads should be defined
            # and data from aviary and qmf coerced in sage to fit
            # the definition.  Side note, aviary data natively is
            # closer to what could be/is a canonical form...
            if "!!descriptors" in ads:
                desc = self.get_desc(ads["!!descriptors"], x)
                if desc == "com.redhat.grid.Expression":
                    type = "expression"
        return type

    def gen_item(self, name, value, cls, path=None, dtype=None,
                 error=None, orig=None):
        """ Generate a dict with name, value, type, error, path,
        property, orig

            This is called with raw GetAd data and with processed data
            from a form submit. With raw data, only the name and value
            will be present.  With form data, we might have a path,
            dtype, or error. dtype is the data type that was
            remembered from the raw data.
        """

        idict = dict()
        idict["name"] = name
        idict["value"] = value
        idict["orig"] = value
        idict["type"] = dtype

        if dtype == "string":
            idict["value"] = strip_string_quotes(value)

        if orig:
            idict["orig"] = orig

        if error and "error" in error:
            idict["error"] = error["error"]

        if name in cls.ad_properties_by_name:
            idict["property"] = cls.ad_properties_by_name[name]

        if path:
            idict["path"] = path

        return idict
    
class FastViewJobAdsSet(JobAdsSet):
    def __init__(self, app, name):
        super(FastViewJobAdsSet, self).__init__(app, name)
    
    def do_get_items(self, session):
        ad_list = self.items.get(session)
        error = self.qmf_error.get(session)
        
        if not ad_list and not error:
            ad_list = list()
            error = None
            results = self.get_job_ad(session)
            if results.error:
                error = results.error    
            elif self.do_check_viewable:
                error = self.check_job_owner(session, results.data['JobAd'])
            self.qmf_error.set(session, error)
            ads = results.data['JobAd']
            cls = self.app.model.job_meta_data
            ad_list = [self.gen_item(x, ads[x], cls, dtype=self.get_type(ads, x)) \
                       for x in ads if not x.startswith("!!") and x in self.app.fast_view_attributes]
            self.items.set(session, ad_list)

        return ad_list, error    
      

class JobPropertyRenderer(TemplateRenderer):
    def render_title(self, session, item):
        title = item["name"]
        if "property" in item:
            property = item["property"]
            if property.title:
                title = property.get_title(session)
        return escape_amp(title)

    def render_value(self, session, item):
        value = item["value"]
        if "property" in item:
            property = item["property"]
            if property.renderer:
                value = property.renderer(session, value)
        if item["type"] == "dict":
            return value
        else:
            ret = escape_entity(str(value))
            return self.insert_breaks(ret)

    def insert_breaks(self, value):
        subwords = list()
        snippets = parse(value, begin_delim="&", end_delim=";")
        for snippet in snippets:
            while len(snippet) > 40:
                subwords.append(snippet[:40])
                snippet = snippet[40:]
            subwords.append(snippet)

        return "&#8203;".join(subwords)

    def render_inline_help(self, session, item):
        if "property" in item:
            property = item["property"]
            return property.description
        
    def render_id(self, session, item):
        return item["property"].name     

class JobAdsGroups(Widget):
    def __init__(self, app, name):
        super(JobAdsGroups, self).__init__(app, name)

        self.group_tmpl = WidgetTemplate(self, "group_html")
        self.error_tmpl = WidgetTemplate(self, "error_html")

    def render_groups(self, session):
        writer = Writer()

        # check for qmf error
        _, error = self.parent.do_get_items(session)
        if error:
            msg = (hasattr(error, "args") and \
                   len(error.args) > 0 and error.args[0]) or ""
            if not msg:
                # probably a timeout exception
                msg = "Unable to get Job information at this time"
            self.error_tmpl.render(writer, session, msg)
        else:
            for group in self.app.model.get_ad_groups():
                self.group_tmpl.render(writer, session, group)

        return writer.to_string()

    def render_group_name(self, session, group):
        return group

    def render_properties(self, session, group):
        items, error = self.parent.get_group_items(session, group)
        writer = Writer()

        for item in items:
            self.parent.item_renderer.render(writer, session, item)

        return writer.to_string()

    def render_error_msg(self, session, msg):
        return msg

class JobAdsViewer(JobAdsSet):
    def __init__(self, app, name):
        super(JobAdsViewer, self).__init__(app, name)

        self.item_renderer = JobPropertyRenderer(self, "property_html")

        self.groups = JobAdsGroups(app, "groups");
        self.add_child(self.groups)

        self.wait = Wait(app, "wait")
        self.add_child(self.wait)

        self.edit_button = JobAdsEditButton(app, "edit_button")
        self.add_child(self.edit_button)

        self.defer_enabled = True
        self.update_enabled = True

    def do_render(self, session):
        # Set redirect if the submission object we depend on is missing
        if self.frame.object.get(session) is None:
            nsession = session.branch()
            frame = self.frame.parent.parent
            frame.view.show(nsession)
            submission_list_url = nsession.marshal()
            self.page.redirect.set(session, submission_list_url)
            session.add_notice(Notice("The submission being displayed became unavailable"))
        else:
            return super(JobAdsViewer, self).do_render(session)

        self.do_check_viewable = False

    def render_edit_button(self, session):
        _, error = self.do_get_items(session)
        render = True
        #We check the JobStatus to see if the job is already completed.  
        #If it is, we do not want to show the "edit" button
        for item in _:
            if "property" in item:
                if item["name"] == "JobStatus":
                    status = item["value"]
                    if JobStatusInfo.get_status_string(status) in {"Completed",
                                                                   "Removed"}:
                        render = False
                    break                   
        return render and not error and self.edit_button.render(session) or ""

    def render_title(self, session):
        return "Attributes"

    def get_group_items(self, session, group):
        group_items = list()

        items, error = self.do_get_items(session)
        for item in items:
            if "property" in item:
                property = item["property"]
                item_group = property.group
            else:
                item_group = "Other"
            if item_group == group:
                group_items.append(item)

        return group_items, error
    
class FastViewJobAdsViewer(FastViewJobAdsSet):
    def __init__(self, app, name):
        super(FastViewJobAdsViewer, self).__init__(app, name)
        
        self.item_renderer = JobPropertyRenderer(self, "property_html")

        self.wait = Wait(app, "wait")
        self.add_child(self.wait)

        self.defer_enabled = True
        self.update_enabled = True

    def render_title(self, session):
        return "Attributes"

    def get_group_items(self, session, group):
        group_items = list()

        items, error = self.do_get_items(session)
        for item in items:
            if "property" in item:
                property = item["property"]
                item_group = property.group
            else:
                item_group = "Other"
            if item_group == group:
                group_items.append(item)

        return group_items, error
    
    def render_all_ordered_properties(self, session):
        items, error = self.do_get_items(session)
        writer = Writer()
        viewable_items = self.app.fast_view_attributes
        for viewable_item in viewable_items:
            for item in items:
                if item["name"] == viewable_item:
                    self.item_renderer.render(writer, session, item)
                    break
        return writer.to_string()                    
    
class JobAdsEditButton(Widget):
    def render_edit_ads_url(self, session):
        branch = session.branch()
        self.parent.frame.show_ads_edit(branch)
        return branch.marshal()

class JobAdsEditor(JobAdsViewer, CuminForm):
    def __init__(self, app, name):
        super(JobAdsEditor, self).__init__(app, name)

        # self.ads will hold all the field values when the edit form
        # is submitted.  How self.ads is created and used is not
        # immediately apparent, so here is a brief overview 
        # (with lots of details left out).

        # Because this class is derived from JobAdsViewer, it has a
        # JobAdsGroup as a child. During rendering of the JobAdsGroup, 
        # do_get_items() below is called and each element of the result is
        # passed to EditablePropertyRenderer.render_value().
        # (look to JobAdsGroup.render_properties() for these calls)

        # In do_get_items(), item["path"] is set to self.ads.path for each
        # item.  This allows EditablePropertyRenderer to create html elements
        # with names based on self.ads.path and other elements of each item.
        # When the form is submitted, the POST request contains name/value pairs
        # for all the html elements marshaled into a URL.

        # The unmarshaling process results in a dictionary of all the job 
        # attributes on the edit page stored in the session under self.ads.path.
        # This dictionary is what is processed in process_submit() below.

        # Note that EditablePropertyRenderer creates hidden html elements
        # for each item which contain original value and type information in
        # addition to an input element.  These extra fields are important
        # in process_submit().
        self.ads = DictParameter(app, "params")
        self.add_parameter(self.ads)

        self.item_renderer = EditablePropertyRenderer(self, "property_html")
        
        self.update_enabled = False

    def do_get_items(self, session, setpath=True):
        items, error = super(JobAdsEditor, self).do_get_items(session)
        if error:
            items = []

        # Avoid an extra pass if we don't need it
        if setpath:
            for item in items:
                item["path"] = self.ads.path
        return items, error

    def process_cancel(self, session):
        branch = session.branch()
        self.ads.set(branch, None) # otherwise url is too long
        self.frame.show_ads_view(branch)
        self.page.redirect.set(session, branch.marshal())

    def process_submit(self, session):

        def can_be_float(val):
            try:
                f = float(val)
                return True
            except:
                return False

        def has_double_quotes(value):
            return value[:1] == "\"" and value[-1:] ==  "\""

        # Check to see if the job is owned by the logged in user.
        # At this point, the only way to do this check is request
        # the job ad again.  Maybe not efficient.
        if self.do_check_viewable:
            results = self.get_job_ad(session)
            if results.error:
                error = results.error
            else:
                error = self.check_job_owner(session, 
                                             results.data['JobAd'])
            if error:
                self.qmf_error.set(session, error)
                self.process_cancel(session)
                return

        ads = self.ads.get(session)

        just_ads = dict()
        for field in ads:            
            ads[field]["error"] = None
            try:
                fval = ads[field]["value"]
            except KeyError:
                ads[field]["value"] = ""
                fval = ""
            ftype = ads[field]["type"]
            if ftype == "integer":
                try:
                    fval = int(fval)
                except:
                    # okay, if there are no double quotes and it's not
                    # a float, go ahead and let condor try to accept this 
                    # as an expression
                    if has_double_quotes(fval) or can_be_float(fval):
                        ads[field]["error"] = "Integer value expected"
                    else:
                        ftype = "expression"
    
            elif ftype == "float":
                try:
                    fval = float(fval)
                except:
                    # okay, if there are no double quotes then let
                    # condor try to accept this as an expression
                    if has_double_quotes(fval):
                        ads[field]["error"] = "Floating point value expected"
                    else:
                        ftype = "expression"
            else:
                fval = unicode(fval)

            if "orig" in ads[field]:
                orig = ads[field]["orig"]
                if ftype == "integer":
                    orig = int(orig)
                elif ftype == "float":
                    orig = float(orig)
                elif ftype == "string":
                    # For ftype == "string", we want to insure double quotes. 
                    # This is due to the convention in the condor plugins which
                    # treats strings with double quotes as string literals and 
                    # all other strings as expressions.  And quotes were stripped
                    # on the way in.
                    # Expressions should be marked with ftype == "expression"
                    # although the value is still a string.

                    # make sure we have quotes on new val and original...
                    fval = "\"%s\"" % strip_string_quotes(fval)
                    orig = "\"%s\"" % strip_string_quotes(orig)

                elif ftype == "expression":
                    # Might as well prevent user from inadvertently changing
                    # an expression into a string by adding double quotes
                    fval = strip_string_quotes(fval)

                if fval != orig:
                    just_ads[unicode(field)] = fval

        # Use the full job add data to find out which 
        # ads are writable.  This info is not available
        # in the POST request data.
        if just_ads:
            items, error = self.do_get_items(session, setpath=False)
            if error:
                msg = (hasattr(error, "args") and \
                           len(error.args) > 0 and error.args[0]) or ""
                if not msg:
                    msg = "Unable to get Job information at this time"
                session.add_notice(Notice("Job edit failed: %s" % msg))
                just_ads = []
            else:    
                writables = dict()
                for item in items:
                    n = item["name"]
                    if n in just_ads:
                        p = "property" in item and item["property"] or None
                        writables[n] = not p or p.writable

        # Process all cases, including errors, becase we
        # want to see a banner for errors we detect.
        id = self.frame.id.get(session)
        scheduler = self.frame.get_scheduler(session, id)
        job_id = self.frame.job_id.get(session)
        submission = self.frame.get_submission(session, id)

        task = self.frame.set_ad_task
        for field in just_ads:
            if not writables[field]:
                ads[field]["error"] = "Attribute is not writable"
            task.invoke(session, scheduler, job_id, field, 
                        str(just_ads[field]), ads[field]["error"],
                        submission)
        self.process_cancel(session)

class OutputFile(Widget):
    err_msg = "Output, Error, and UserLog file names are invalid."
    def __init__(self, app, name, which_file, first_last):
        super(OutputFile, self).__init__(app, name)

        self.which_file = which_file
        self.first_last = first_last

        self.defer_enabled = True

    def render_content(self, session):
        id = self.frame.id.get(session)
        submission, job_server, scheduler = self.frame.get_trifecta(session, id)
        job_id = self.frame.job_id.get(session)
        state, file, start, end = self.get_file_args(session)
        
        if file:
            result = self.app.remote.fetch_job_data(job_server, job_id, state, 
                                                    file, start, end, 
                                                    scheduler.Name,
                                                    submission,
                                                    default={'Data': ""})
            if result.error:
                return result.status
            return escape_entity(result.data['Data'])
        return self.err_msg

    def get_file_args(self, session):
        first_last = self.first_last.get(session)
        if first_last == "t":
            start = -2048
            end = 0
        else:
            start = 0
            end = 2048
        state = self.which_file.get_current_state(session)
        file = self.which_file.get_file_name(session, state)
        return (state, file, start, end)

    def render_loading(self, session, *args):
        file = self.which_file.get_current_file_name(session)
        return file and "loading..." or self.err_msg

class JobOutput(JobAdsSet, Form):
    def __init__(self, app, name, check_viewable):
        super(JobOutput, self).__init__(app, name)

        self.which_file = self.FileSwitch(app, "file")
        self.add_child(self.which_file)

        self.first_last = self.FLSwitch(app, "first_last")
        self.add_child(self.first_last)

        self.__fetch = self.FetchButton(app, "refresh")
        self.add_child(self.__fetch)

        self.output = OutputFile(app, "job_output", self.which_file, self.first_last)
        self.add_child(self.output)

        self.do_check_viewable = check_viewable

    def render_title(self, session):
        return "Output"

    def render_is_tail(self, session):
        tail = self.first_last.get(session)
        return tail == "t" and "1" or "0"

    def render_out_time(self, session):
        now = datetime.now()
        return fmt_datetime(now, sec=True)

    def do_process(self, session):

        def add_path(path, filename):
            if path is not None and filename not in (None, ""):
                return os.path.join(path, filename)
            return filename

        out_file = None
        user_file = None
        err_file = None
        iwd = None

        ads, error = self.do_get_items(session)
        if error:
            msg = (hasattr(error, "args") and \
                   len(error.args) > 0 and error.args[0]) or ""
            self.set_redirect(session, self.frame.parent, msg)

        for ad in ads:
            if ad['name'] == "Out":
                out_file = ad['value']
            elif ad['name'] == "UserLog":
                user_file = ad['value']
            elif ad['name'] == "Err":
                err_file = ad['value']
            elif ad['name'] == "Iwd":
                # Save working directory for path
                # extension on the above files...
                iwd = ad['value']

        if iwd is not None:
            out_file = add_path(iwd, out_file)
            err_file = add_path(iwd, err_file)
            user_file = add_path(iwd, user_file)

        # set title for radiotab so mouseover will display file name
        self.which_file.set_file_name(session, "o", out_file)
        self.which_file.set_file_name(session,"e", err_file)
        self.which_file.set_file_name(session,"u", user_file)

        if self.which_file.is_bad(out_file):
            self.which_file.disable(session, "o")
        if self.which_file.is_bad(err_file):
            self.which_file.disable(session, "e")
        if self.which_file.is_bad(user_file):
            self.which_file.disable(session, "u")

        return super(JobOutput, self).do_process(session)

    class FetchButton(FormButton):
        def render_content(self, session):
            return "Refresh"

    class FileSwitch(StateSwitch):
        def __init__(self, app, name):
            super(JobOutput.FileSwitch, self).__init__(app, name)

            self.add_state("o", "Output")
            self.add_state("e", "Error")
            self.add_state("u", "UserLog")

            self.disabled = self.DisabledList(app, "disabled")
            self.add_attribute(self.disabled)

            self.link_titles = self.Titles(app, "link_titles")
            self.add_attribute(self.link_titles)

        class DisabledList(Attribute):
            def get_default(self, session):
                return list()

        class Titles(Attribute):
            def get_default(self, session):
                return dict()

        def disable(self, session, state):
            disabled = self.disabled.get(session)
            disabled.append(state)
            self.disabled.set(session, disabled)
            if state == self.get(session):
                self.select_first_enabled(session)

        def set_file_name(self, session, state, link_title):
            link_titles = self.link_titles.get(session)
            link_titles[state] = link_title
            self.link_titles.set(session, link_titles)

        def get_file_name(self, session, state):
            link_titles = self.link_titles.get(session)
            return state in link_titles and link_titles[state] or ""

        def get_current_file_name(self, session):
            state = self.get(session)
            return self.get_file_name(session, state)

        def get_current_state(self, session):
            return self.get(session)

        def select_first_enabled(self, session):
            states = self.get_items(session)
            disabled = self.disabled.get(session)
            for state in states:
                if not state in disabled:
                    self.set(session, state)
                    break

        def render_item_link(self, session, state):
            branch = session.branch()
            self.set(branch, state)

            title = self.get_title(state)
            link_titles = self.link_titles.get(session)
            link_title = state in link_titles and link_titles[state] or ""
            disabled = self.disabled.get(session)
            if state in disabled:
                class_ = "disabled"
                href = "javascript:void(0)"
            else:
                class_ = self.get(session) == state and "selected"
                href = branch.marshal()
            return fmt_link(href, title, class_, link_title=link_title)

        def is_bad(self, file):
            bad = False
            if not file:
                bad = True
            elif "/dev/null" in file.lower():
                bad = True
            return bad


    class FLSwitch(StateSwitch):
        def __init__(self, app, name):
            super(JobOutput.FLSwitch, self).__init__(app, name)

            self.add_state("t", "Tail", "Display end of file")
            self.add_state("h", "Head", "Display beginning of file")

class JobActionForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task, verb):
        super(JobActionForm, self).__init__(app, name, task)

        self.reason = ReasonField(app, "reason")
        self.reason.required = True
        self.add_field(self.reason)

        self.job_id = Parameter(app, "job_id")
        self.add_parameter(self.job_id)

        self.verb = verb

    def get_reason(self, session, verb):
        """ returns <verb> by username[: <user input reason>] """
        reason = self.reason.get(session)
        if reason:
            reason = [reason]
            user = session.client_session.attributes["login_session"].user

            verb_by = "%s by %s" % (verb, user.name)
            reason.insert(0, verb_by)
            return ": ".join(reason)

    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            id = self.id.get(session)
            scheduler = self.task.frame.get_scheduler(session, id)
            reason = self.get_reason(session, self.verb)
            job_id = self.job_id.get(session)
            submission = self.task.frame.get_submission(session, id)
            self.task.invoke(session, scheduler, job_id, reason, submission)
            self.task.exit_with_redirect(session)

    def validate(self, session):
        super(JobActionForm, self).validate(session)
        if not self.errors.get(session) and \
               self.app.authorizator.is_enforcing():
            id = self.id.get(session)

            # Make sure that the job belongs to the designated submission.
            job_id = self.job_id.get(session)
            okay, frame, message = \
                self.task.frame.check_submission_membership(session, id, job_id)
            if not okay:
                if not message:
                    message = "Unable to verify this job" \
                              " is a member of the submission"
                f = FormError(message)
                self.errors.add(session, f)
                return

            # Check here to make sure the logged in user owns
            # the submission and job or is an admin
            login = session.client_session.attributes["login_session"]
            if "admin" not in login.group:
                user = login.user.name
                submission = self.task.frame.get_submission(session, id)
                if hasattr(submission, "Owner") and submission.Owner != user:
                    f = FormError("The logged in user does not "\
                                  "own this submission.")
                    self.errors.add(session, f)
  
class ReasonField(NoXMLStringField):
    def render_title(self, session):
        return "Reason"

class JobAction(ObjectFrameTask):
    def __init__(self, app, frame, verb, cmd):
        super(JobAction, self).__init__(app, frame)

        self.form = JobActionForm(app, self.name, self, verb)
        self.cmd = cmd

    def do_enter(self, session, osession):
        job_id = self.frame.job_id.get(osession)
        self.form.job_id.set(session, job_id)

    def do_invoke(self, invoc, scheduler, job_id, reason, submission):
        self.app.remote.control_job(self.cmd, scheduler, job_id, 
                                    reason, submission,
                                    callback=invoc.make_callback())

class JobHold(JobAction):
    def __init__(self, app, frame):
        super(JobHold, self).__init__(app, frame, "held", "holdJob")

    def get_title(self, session):
        return "Hold Job"

class JobRelease(JobAction):
    def __init__(self, app, frame):
        super(JobRelease, self).__init__(app, frame, "released", "releaseJob")

    def get_title(self, session):
        return "Release Job"

class JobSuspend(JobAction):
    def __init__(self, app, frame):
        super(JobSuspend, self).__init__(app, frame, "suspended", "suspendJob")

    def get_title(self, session):
        return "Suspend Job"

class JobContinue(JobAction):
    def __init__(self, app, frame):
        super(JobContinue, self).__init__(app, frame, "continued", "continueJob")

    def get_title(self, session):
        return "Continue Job"

class JobRemove(JobAction):
    def __init__(self, app, frame):
        super(JobRemove, self).__init__(app, frame, "removed", "removeJob")

    def get_title(self, session):
        return "Remove Job"

    def do_enter(self, session, osession):
        super(JobRemove, self).do_enter(session, osession)

        nsession = osession.branch()

        # return to the job list page
        job_list = self.frame.parent
        job_list.view.show(nsession)

        self.form.return_url.set(session, nsession.marshal())

class JobSetAttribute(ObjectFrameTask):
    def __init__(self, app, frame):
        super(JobSetAttribute, self).__init__(app, frame)
        
        # Since we don't actually want to see this on the job view page
        self.visible=False
        
    def get_title(self, session):
        pass

    def get_description(self, session):
        return "Edit Ad"

    def do_invoke(self, invoc, scheduler, job_id, name, value, error, submission):
        # Don't make the call, but we want to see the banner
        # so invoke the callback directly with the error as status
        if error:
            invoc.make_callback()(name + ": " + str(error), None)
        else:    
            self.app.remote.set_job_attribute(scheduler, 
                                              job_id, name, value,
                                              invoc.make_callback(), 
                                              submission)

