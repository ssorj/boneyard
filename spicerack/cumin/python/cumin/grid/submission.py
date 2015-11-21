import logging
import shlex
from random import choice
import os
import datetime

from job import JobSelector, JobFrame
from cumin.objectframe import ObjectFrame, ObjectView, ObjectViewSummary, ObjectViewContext
from cumin.sqladapter import ObjectSqlAdapter
from cumin.objectselector import ObjectSelector, ObjectLinkColumn,\
    ObjectTableColumn, ObjectTable, SelectableSearchObjectTable
from cumin.task import TaskLink, Task, ObjectTaskForm
from cumin.parameters import ObjectAttribute
from cumin.util import xml_escape

from rosemary.sqlfilter import SqlFilter, SqlLikeFilter, SqlValueFilter, SqlDateValueFilter
from rosemary.sqlquery import SqlInnerJoin

from wooly.util import StringCatalog
from wooly.forms import StringField, ScalarField, FormError, OptionInputSet,\
    MultilineStringField, FormField, IntegerField, LabelFormField, NoXMLStringField
from wooly.parameters import IntegerParameter, StringParameter


log = logging.getLogger("cumin.grid.submission")

class SubmissionFrame(ObjectFrame):
    def __init__(self, app, name, check_viewable=False):
        cls = app.model.com_redhat_grid.Submission

        super(SubmissionFrame, self).__init__(app, name, cls)

        # This will check whether or not the selected submission
        # object is viewable by the logged in user during the
        # processing pass.
        self.do_check_viewable = check_viewable

        self.job = JobFrame(app, "job", self.object, check_viewable)
        self.add_mode(self.job)

        jobs = JobSelector(app, "jobs", self.object)
        self.view.add_tab(jobs)

    def not_viewable_redirect(self):
        return (self.parent, 
                "Logged in user does not own the specified submission")

class PoolSubmissionFrame(SubmissionFrame):
    # Use an ObjectView derivation here so that
    # SubmissionFrame can use a different summary class later on...
    def get_view(self, app, name, obj):
        return self.MyObjectView(app, name, obj)

    class MyObjectView(ObjectView):
        def get_summary(self, app, name, obj):
            return PoolSubmissionFrame.MyObjectViewSummary(app, name, obj)
    
    class MyObjectViewSummary(ObjectViewSummary):
        def get_scheduler(self, session):
            # Find out submission
            subm = self.frame.get_object(session, 
                                         self.frame.id.get(session))

            # Get a scheduler...
            js = self.app.model.get_jobserver_from_submission(session, subm)
            return self.app.model.get_scheduler_from_jobserver(session, js)

        def render_auxlink(self, session):
            sch = self.get_scheduler(session)
            frame = self.page.page_widgets_by_path["main.grid.scheduler"]
            return frame.get_href(session, sch._id)

        def render_auxtitle(self, session):
            sch = self.get_scheduler(session)
            return "Scheduler '%s'" % xml_escape(sch.Name)
    
class SubmissionData(ObjectSqlAdapter):
    def __init__(self, app):
        submission = app.model.com_redhat_grid.Submission
        jobserver = app.model.com_redhat_grid.JobServer

        super(SubmissionData, self).__init__(app, submission)

        self.add_join(jobserver, submission.jobserverRef, jobserver._id)

        filter = FreshnessFilter(submission)
        self.query.add_filter(filter)

class FreshnessFilter(SqlFilter):
    def __init__(self, cls):
        super(FreshnessFilter, self).__init__()

        table = cls.sql_table

        fmt = "(%s > now() - interval '10 days' or %s > 0 or %s > 0 or %s > 0)"
        args = (table._qmf_update_time.identifier,
                table.Idle.identifier,
                table.Running.identifier,
                table.Held.identifier)

        self.text = fmt % args

    def emit(self):
        return self.text

class SubmissionSelector(ObjectSelector):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Submission

        super(SubmissionSelector, self).__init__(app, name, cls)

        self.table.adapter = SubmissionData(app)

        col = self.QDateColumn(app, cls.QDate.name, cls.QDate)
        self.add_column(col)

        self.add_attribute_column(cls.Idle)
        self.add_attribute_column(cls.Running)
        self.add_attribute_column(cls.Completed)
        self.add_attribute_column(cls.Held)
        self.add_attribute_column(cls.Suspended)
        
        self.field_param = StringParameter(app, "field_param")
        self.add_parameter(self.field_param)
        
        self.select_input = self.SubmissionFieldOptions(app, self.field_param)
        self.add_selectable_search_filter(self.select_input)
           
    class QDateColumn(ObjectTableColumn):
        def _get_raw_content(self, session, data):
            d = super(SubmissionSelector.QDateColumn, self).\
                         render_cell_content(session, data)
            if d is None:
                d = "unknown"
            return d

        def render_cell_content(self, session, data):
            # Abbreviate to the time or the date, and we'll give
            # the whole value in the cell title on hover
            d = self._get_raw_content(session, data)
            if type(d) is datetime.datetime:
                if datetime.datetime.now() - d < datetime.timedelta(days=1):
                    d = d.time()
                else:
                    d = d.date()
            return d

        def render_cell_title(self, session, data):
            return self._get_raw_content(session, data)

    class SubmissionFieldOptions(SelectableSearchObjectTable.SearchFieldOptions):
        def __init__(self, app, param):
            super(SubmissionSelector.SubmissionFieldOptions, self).__init__(app, param)
            self.cls = app.model.com_redhat_grid.Submission
            
        def do_get_items(self, session):
            return [self.cls.Name, self.cls.Owner, self.cls.QDate, self.cls.Idle, \
                    self.cls.Running, self.cls.Completed, self.cls.Held, self.cls.Suspended]

class PoolSubmissionSelector(SubmissionSelector):
    def __init__(self, app, name, frame="main.grid.submission"):
        super(PoolSubmissionSelector, self).__init__(app, name)
       
        col = self.PoolSubmissionObjectLinkColumn(app, "name", self.cls.Name, self.cls._id, frame)
        self.insert_column(0, col)
        #self.add_search_filter(col)

        attr = self.cls.Owner
        col = ObjectTableColumn(app, attr.name, attr)
        self.insert_column(1, col)

        # Removed PoolSubmitLink, derived from TaskLink, because the
        # the only method supplied was do_enter which does not exist
        # in the parent.  There are do_enter methods on Tasks,
        # but not on TaskLinks; this was probably a mistake. 06/7/2001
        link = TaskLink(app, "job_submit", app.grid.job_submit)
        self.links.add_child(link)

        link = TaskLink(app, "dag_job_submit", app.grid.dag_job_submit)
        self.links.add_child(link)

        link = TaskLink(app, "vm_job_submit", app.grid.vm_job_submit)
        self.links.add_child(link)
        
    
    def create_table(self, app, name, cls):
        return SelectableSearchObjectTable(app, name, cls)    

    class PoolSubmissionObjectLinkColumn(ObjectLinkColumn):      
        def render_cell_content(self, session, record):
            retval = len(record) > 0 and record[self.field.index] or ""
            if(len(record[self.field.index]) > 50):
                retval = record[self.field.index][:50] + "..."  #indicate that we truncated the name
            return retval       

class PoolSubmissionJoinSelector(PoolSubmissionSelector):
    def __init__(self, app, name):
        super(PoolSubmissionJoinSelector, self).__init__(app, name)

        scheduler = app.model.com_redhat_grid.Scheduler
        self.SchedulerJoin(app, self.table.adapter.query, self.cls.sql_table,
                     self.cls.jobserverRef.sql_column, "jid")
        
        #frame = "main.grid.scheduler"
        #col = self.SchedulerColumn(app, "Scheduler", scheduler.Name, scheduler._id, frame)
        #self.insert_column(2, col)

        self.enable_csv_export()

    class SchedulerColumn(ObjectLinkColumn):
        def render_header_content(self, session):
            return self.name

    class SchedulerJoin(SqlInnerJoin):
        """ Connects Submission->jobserverRef->schedulerRef->Scheduler """

        def __init__(self, app, query, table, this, that):
            super(PoolSubmissionJoinSelector.SchedulerJoin, self).__init__(query, table, this, that)

            self.adapter = self.SchedulerData(app)

        def emit(self):
            scheduler_select = self.adapter.query.emit(self.adapter.columns)

            args = (scheduler_select, self.this, self.that)

            return "inner join (%s) as \"Scheduler\" on %s = %s" % args

        class SchedulerData(ObjectSqlAdapter):
            def __init__(self, app):
                jobserver = app.model.com_redhat_grid.JobServer
                scheduler = app.model.com_redhat_grid.Scheduler

                super(PoolSubmissionJoinSelector.SchedulerJoin.SchedulerData, self).__init__(app, jobserver)

                self.add_join(scheduler, jobserver.schedulerRef, scheduler._id)

                self.columns = list()

                # avoid conflict with scheduler._id
                job_server_id = jobserver._id.sql_column.identifier
                self.columns.append("%s as jid" % job_server_id)

                self.columns.append(jobserver.schedulerRef.sql_column)
                self.columns.append(scheduler._id.sql_column)
                self.columns.append(scheduler.Name.sql_column)

class JobDescriptionField(NoXMLStringField):
    def __init__(self, app, name):
        super(JobDescriptionField, self).__init__(app, name)

        self.input.size = 50
        self.required = True

    def render_title(self, session):
        return "Description"

    def render_help(self, session):
        return "This text will identify the submission"
 
class JobSchedulerField(ScalarField):
    def __init__(self, app, name):
        super(JobSchedulerField, self).__init__(app, name, None)

        self.param = IntegerParameter(app, "param")
        self.add_parameter(self.param)

        cls = self.app.model.com_redhat_grid.Scheduler

        self.object = ObjectAttribute(self, "object", cls, self.param)
        self.add_attribute(self.object)

        self.input = self.SchedulerOptions(app, "input", self.param)
        self.add_child(self.input)

    def get(self, session):
        return self.object.get(session)

    def validate(self, session):
        super(JobSchedulerField, self).validate(session)

        schedulers = self.input.get_items(session)

        if not schedulers:
            error = FormError("There is no schedd to submit to")
            self.form.errors.add(session, error)

    def render_title(self, session):
        return "Schedd"

    def render_help(self, session):
        return "Submit the job to this schedd"

    class SchedulerOptions(OptionInputSet):
        def do_process(self, session):
            cls = self.app.model.com_redhat_grid.Scheduler
            id = self.param.get(session)

            if id is None:
                items = self.get_items(session)

                if items:
                    scheduler = choice(items)
                    self.param.set(session, scheduler._id)

            super(JobSchedulerField.SchedulerOptions, self).do_process \
                (session)

        def do_get_items(self, session):
            cls = self.app.model.com_redhat_grid.Scheduler
            schedulers = cls.get_selection(session.cursor)
            return schedulers

        def render_item_value(self, session, item):
            return item._id

        def render_item_content(self, session, item):
            return xml_escape(item.Name)

        def render_item_selected_attr(self, session, item):
            if item._id == self.param.get(session):
                return "selected=\"selected\""

class JobAttributesField(MultilineStringField):
    def __init__(self, app, name):
        super(JobAttributesField, self).__init__(app, name)

        self.input.columns = 50

        self.illegal_attributes = ("owner", "user")

    def render_title(self, session):
        return "Extra attributes"

    def parse_attributes(self, session):
        attrs = dict()

        text = self.get(session)
        text = text.strip()

        for line in text.split("\n"):
            line = line.strip()

            if not line:
                continue

            try:
                name, value = self.parse_attribute(line)
            except:
                msg = "Failed parsing attribute '%s'" % line
                self.form.errors.get(session).append(FormError(msg))

                continue

            if name.lower() in self.illegal_attributes:
                msg = "Setting extra attribute '%s' is prohibited" % name
                self.form.errors.get(session).append(FormError(msg))

                continue

            attrs[name] = value

        return attrs

    def parse_attribute(self, line):
        name, value = line.split("=", 1)

        name = name.strip()
        value = self.unmarshal_value(value.strip())

        return name, value

    def unmarshal_value(self, value):
        if value.lower() == "true":
            return True

        if value.lower() == "false":
            return False

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        return value

class JobSubmit(Task):
    def __init__(self, app):
        super(JobSubmit, self).__init__(app)

        self.form = JobSubmitForm(app, self.name, self)

    def get_title(self, session, scheduler):
        return "Submit job"

    def do_invoke(self, session, scheduler, invoc,
                  description,
                  executable,
                  arguments=None,
                  requirements=None,
                  universe=None,
                  iwd=None,
                  stdin=None,
                  stdout=None,
                  stderr=None,
                  usrlog=None,
                  request_mem_MB=None,
                  request_disk_KB=None,
                  attrs={}):

        def add_path(path, filename):
            if path is not None and filename not in (None, ""):
                return os.path.join(path, filename)
            return filename

        # fixup paths for in, out, err, log
        if iwd is not None:
            stdin = add_path(iwd, stdin)
            stdout = add_path(iwd, stdout)
            stderr = add_path(iwd, stderr)
            usrlog = add_path(iwd, usrlog)

        ad = dict()

        ad["Submission"] = description
        ad["Owner"] = invoc.user.name
        ad["Cmd"] = executable

        def put(name, value):
            if value:
                ad[name] = value

        put("Args", arguments)
        put("Iwd", iwd)
        put("Requirements", requirements)
        put("JobUniverse", universe)
        put("In", stdin)
        put("Out", stdout)
        put("Err", stderr)
        put("UserLog", usrlog)
        put("RequestMemory", request_mem_MB)
        put("RequestDisk", request_disk_KB)

        ad.update(standard_job_attributes)
        ad.update(attrs)

        descriptors = dict()
        descriptors["Requirements"] = "com.redhat.grid.Expression"

        ad["!!descriptors"] = descriptors

        invoc.description = "Submit job '%s'" % description

        log_job_ad(ad)

        self.app.remote.submit_job(scheduler, ad, invoc.make_callback())

class JobSubmitForm(ObjectTaskForm):
    def __init__(self, app, name, task):
        cls = app.model.com_redhat_grid.Scheduler
        super(JobSubmitForm, self).__init__(app, name, task, cls)

        self.description = JobDescriptionField(app, "description")
        self.add_field(self.description)

        self.command = self.CommandField(app, "command")
        self.command.input.columns = 50
        self.command.required = True
        self.command.help = "The path to the executable and any arguments"
        self.add_field(self.command)

        self.requirements = self.RequirementsField(app, "requirements")
        self.requirements.input.columns = 50
        self.requirements.required = True
        self.requirements.help = "Attributes controlling where and when " + \
            "this job will run"
        self.add_field(self.requirements)

        self.directory = self.WorkingDirectoryField(app, "directory")
        self.directory.input.size = 50
        self.directory.required = True
        self.directory.help = "Run the process in this directory"
        self.add_field(self.directory)

        self.scheduler = JobSchedulerField(app, "scheduler")
        self.add_extra_field(self.scheduler)

        self.universe = self.UniverseField(app, "universe")
        self.add_extra_field(self.universe)

        self.stdin = self.StdinField(app, "stdin")
        self.stdin.input.size = 50
        self.stdin.help = "Get process input from this file"
        self.add_extra_field(self.stdin)

        self.stdout = self.StdoutField(app, "stdout")
        self.stdout.input.size = 50
        self.stdout.help = "Send process output to this file"
        self.add_extra_field(self.stdout)

        self.stderr = self.StderrField(app, "stderr")
        self.stderr.input.size = 50
        self.stderr.help = "Send error output to this file"
        self.add_extra_field(self.stderr)

        self.usrlog = self.UsrLogField(app, "usrlog")
        self.usrlog.input.size = 50
        self.usrlog.help = "User log file"
        self.add_extra_field(self.usrlog)

        self.request_mem_MB = self.RequestMemField(app, "requestmem")
        self.add_extra_field(self.request_mem_MB)

        self.request_disk_MB = self.RequestDiskField(app, "requestdisk")
        self.add_extra_field(self.request_disk_MB)

        #self.options = self.OptionsField(app, "options")
        #self.add_extra_field(self.options)

        self.attrs = JobAttributesField(app, "attrs")
        self.add_extra_field(self.attrs)

    def process_display(self, session):
        self.request_mem_MB.set(session,  self.app.form_defaults.request_memory)
        self.request_disk_MB.set(session, self.app.form_defaults.request_disk)
        self.scheduler.validate(session)

    def process_submit(self, session):
        self.validate(session)

        attrs = self.attrs.parse_attributes(session)

        if not self.errors.get(session):
            scheduler = self.scheduler.get(session)
            description = self.description.get(session)
            command = self.command.get(session)
            requirements = self.requirements.get(session)
            universe = self.universe.get(session)
            directory = self.directory.get(session)
            stdin = self.stdin.get(session)
            stdout = self.stdout.get(session)
            stderr = self.stderr.get(session)
            usrlog = self.usrlog.get(session)
            request_mem_MB = self.request_mem_MB.get(session)
            request_disk_KB = self.request_disk_MB.get(session) * 1024

            tokens = shlex.split(command)

            executable = tokens[0]
            arguments = " ".join(tokens[1:])

            self.task.invoke(session,
                             scheduler,
                             description,
                             executable,
                             arguments=arguments,
                             requirements=requirements,
                             universe=universe,
                             iwd=directory,
                             stdin=stdin,
                             stdout=stdout,
                             stderr=stderr,
                             usrlog=usrlog,
                             request_mem_MB=request_mem_MB,
                             request_disk_KB=request_disk_KB,
                             attrs=attrs)

            self.task.exit_with_redirect(session, scheduler)

    class CommandField(MultilineStringField):
        def render_title(self, session):
            return "Command"

    class RequirementsField(MultilineStringField):
        def render_title(self, session):
            return "Requirements"

    class UniverseField(ScalarField):
        def __init__(self, app, name):
            super(JobSubmitForm.UniverseField, self).__init__ \
                (app, name, None)

            self.param = IntegerParameter(app, "param")
            self.add_parameter(self.param)

            self.input = self.UniverseOptions(app, "input", self.param)
            self.add_child(self.input)

        def render_title(self, session):
            return "Universe"

        class UniverseOptions(OptionInputSet):
            def get_items(self, session):
                return ((None, "Default"),
                        (5, "Vanilla"),
                        (7, "Scheduler"),
                        (9, "Grid"),
                        (10, "Java"),
                        (11, "Parallel"),
                        (12, "Local"),
                        (13, "VM"))

            def render_item_value(self, session, item):
                return item[0]

            def render_item_content(self, session, item):
                return item[1]

    class WorkingDirectoryField(StringField):
        def render_title(self, session):
            return "Working directory"

    class StdinField(StringField):
        def render_title(self, session):
            return "Standard input"

    class StdoutField(StringField):
        def render_title(self, session):
            return "Standard output"

    class StderrField(StringField):
        def render_title(self, session):
            return "Standard error"

    class UsrLogField(StringField):
        def render_title(self, session):
            return "User Log"

    class RequestMemField(IntegerField):
        def render_title(self, session):
            return "Request Memory"

        def render_help(self, session):
            return "Requested memory size (MB), required by " \
                "partitionable slots."

    class RequestDiskField(IntegerField):
        def render_title(self, session):
            return "Request Disk"

        def render_help(self, session):
            return "Requested disk space (MB), required by " \
                "partitionable slots."

    # class OptionsField(CheckboxField):
    #     def __init__(self, app, name):
    #         super(SubmissionAddForm.OptionsField, self).__init__(app, name)

    #         self.add_option(self.SaveAsTemplate(app, "template"))
    #         self.add_option(self.UseCloud(app, "cloud"))

    #     def render_title(self, session):
    #         return "Options"

    #     class SaveAsTemplate(CheckboxFieldOption):
    #         def render_title(self, session):
    #             return "Save as template"

    #     class UseCloud(CheckboxFieldOption):
    #         def render_title(self, session):
    #             return "Use cloud"

class VmJobSubmit(Task):
    def __init__(self, app):
        super(VmJobSubmit, self).__init__(app)

        self.form = VmJobSubmitForm(app, self.name, self)

    def get_title(self, session, scheduler):
        return "Submit VM job"

    def do_invoke(self, session, scheduler, invoc,
                  description, image, memory, attrs={}, request_disk_KB=0):
        ad = dict()

        # General

        ad["Submission"] = description
        ad["Owner"] = invoc.user.name
        ad["Cmd"] = image # This is just an identifier in this context
        ad["Iwd"] = "/tmp"
        ad["JobUniverse"] = 13 # VM
        ad["ShouldTransferFiles"] = "NEVER" # try submit without
        ad["RequestMemory"] = \
            "ceiling(ifThenElse(JobVMMemory =!= undefined," + \
                               "JobVMMemory, " + \
                               "ImageSize / 1024.000000))"
        ad["RequestDisk"] = request_disk_KB

        # VM

        ad["VMPARAM_vm_Disk"] = "%s:vda:w" % image
        ad["JobVMType"] = "kvm"
        ad["JobVMMemory"] = memory
        ad["JobVM_VCPUS"] = 1
        ad["JobVMNetworking"] = False
        ad["JobVMCheckpoint"] = False
        
        # Requirements

        exprs = list()
 
        exprs.append('VM_Type == "KVM"')
        exprs.append('Arch == "X86_64"') # parameterize
        exprs.append('HasVM')
        exprs.append('VM_AvailNum > 0')
        exprs.append('TotalDisk >= DiskUsage')
        exprs.append('TotalMemory >= %i' % memory)
        exprs.append('VM_Memory >= %i' % memory)

        # needs further consideration
        #exprs.append('TARGET.FileSystemDomain == MY.FileSystemDomain')

        ad["Requirements"] = " && ".join(exprs)

        # Extra attributes

        ad.update(standard_job_attributes)
        ad.update(attrs)

        # Descriptors

        descriptors = dict()

        descriptors["RequestMemory"] = "com.redhat.grid.Expression"
        descriptors["Requirements"] = "com.redhat.grid.Expression"

        ad["!!descriptors"] = descriptors

        invoc.description = "Submit VM job '%s'" % description

        log_job_ad(ad)

        self.app.remote.submit_job(scheduler, ad, invoc.make_callback())

class VmJobSubmitForm(ObjectTaskForm):
    def __init__(self, app, name, task):
        cls = app.model.com_redhat_grid.Scheduler
        super(VmJobSubmitForm, self).__init__(app, name, task, cls)

        self.description = JobDescriptionField(app, "description")
        self.add_field(self.description)

        self.image = self.ImageField(app, "image")
        self.image.input.size = 50
        self.image.required = True
        self.add_field(self.image)

        self.note = self.LabelField(app, "kvmnote")
        self.add_field(self.note)

        self.memory = self.MemoryField(app, "memory")
        self.memory.required = True
        self.add_extra_field(self.memory)
        
        self.request_disk_MB = self.RequestDiskField(app, "requestdisk")
        self.add_extra_field(self.request_disk_MB)

        self.scheduler = JobSchedulerField(app, "scheduler")
        self.add_extra_field(self.scheduler)

        self.attrs = JobAttributesField(app, "attrs")
        self.add_extra_field(self.attrs)
        
    def process_display(self, session):
        self.scheduler.validate(session)
        self.memory.set(session, self.app.form_defaults.request_memory_vm)
        self.request_disk_MB.set(session, self.app.form_defaults.request_disk_vm)

    def process_submit(self, session):
        self.validate(session)

        attrs = self.attrs.parse_attributes(session)

        if not self.errors.get(session):
            scheduler = self.scheduler.get(session)
            description = self.description.get(session)
            image = self.image.get(session)
            memory = self.memory.get(session)
            request_disk_KB = self.request_disk_MB.get(session) * 1024

            self.task.invoke(session,
                             scheduler,
                             description,
                             image,
                             memory,
                             attrs=attrs,
                             request_disk_KB=request_disk_KB)

            self.task.exit_with_redirect(session, scheduler)

    class LabelField(LabelFormField):
        ''' this is just text that appears in place of actual form fields '''
        def __init__(self, app, name):
            super(VmJobSubmitForm.LabelField, self).__init__(app, name)
            self.title = "Note:  The default VM job type is KVM."

    class ImageField(StringField):
        def render_title(self, session):
            return "Image location"

        def render_help(self, session):
            return "The path to VM disk image file"

    class MemoryField(IntegerField):
        def render_title(self, session):
            return "Memory"

        def render_help(self, session):
            return "The VM's memory size (MB)"

    class RequestDiskField(IntegerField):
        def render_title(self, session):
            return "Request Disk"
        
        def render_help(self, session):
            return "The VM's image size (MB), required by partitionable slots."

class DagJobSubmit(Task):
    def __init__(self, app):
        super(DagJobSubmit, self).__init__(app)

        self.form = DagJobSubmitForm(app, self.name, self)

    def get_title(self, session, scheduler):
        return "Submit DAG job"

    def do_invoke(self, session, scheduler, invoc,
                  description, dag_location, attrs={}):
        ad = dict()
        
        dag_dir, dag_file = os.path.split(dag_location)

        ad["Submission"] = description
        ad["Owner"] = invoc.user.name
        ad["Cmd"] = "/usr/bin/condor_dagman"
        ad["Iwd"] = dag_dir 
        ad["JobUniverse"] = 7 # Scheduler
        ad["Out"] = "%s.out" % dag_file
        ad["Err"] = "%s.err" % dag_file
        ad["UserLog"] = "%s.log" % dag_file
        ad["Requirements"] = "True"
        ad["RemoveKillSig"] = "SIGUSR1"
        ad["OnExitRemove"] = "ExitSignal =?= 11 || " + \
            "(ExitCode =!= UNDEFINED && ExitCode >= 0 && ExitCode <= 2)"
        ad["CopyToSpool"] = "False"

        args = list()
        args.append("-f")
        args.append("-Debug 3")
        args.append("-allowversionmismatch")
        args.append("-usedagdir")
        args.append("-Lockfile %s.lock" % dag_file)
        args.append("-Dag %s" % dag_location)

        ad["Args"] = " ".join(args)

        vars = list()
        vars.append("_CONDOR_DAGMAN_LOG=%s.out" % dag_file)
        vars.append("_CONDOR_MAX_DAGMAN_LOG=0")

        ad["Environment"] = " ".join(vars)

        ad.update(standard_job_attributes)
        ad.update(attrs)

        descriptors = dict()
        descriptors["Requirements"] = "com.redhat.grid.Expression"
        descriptors["OnExitRemove"] = "com.redhat.grid.Expression"
        descriptors["CopyToSpool"] = "com.redhat.grid.Expression"

        ad["!!descriptors"] = descriptors

        invoc.description = "Submit DAG job '%s'" % description

        log_job_ad(ad)

        self.app.remote.submit_job(scheduler, ad, invoc.make_callback())

class DagJobSubmitForm(ObjectTaskForm):
    def __init__(self, app, name, task):
        cls = app.model.com_redhat_grid.Scheduler
        super(DagJobSubmitForm, self).__init__(app, name, task, cls)

        self.description = JobDescriptionField(app, "description")
        self.add_field(self.description)

        self.location = self.LocationField(app, "location")
        self.location.help = "The path to the DAG job file"
        self.location.required = True
        self.location.input.size = 50
        self.add_field(self.location)

        self.scheduler = JobSchedulerField(app, "scheduler")
        self.add_extra_field(self.scheduler)

        self.attrs = JobAttributesField(app, "attrs")
        self.add_extra_field(self.attrs)

    def process_display(self, session):
        self.scheduler.validate(session)

    def process_submit(self, session):
        self.validate(session)

        attrs = self.attrs.parse_attributes(session)

        if not self.errors.get(session):
            scheduler = self.scheduler.get(session)
            description = self.description.get(session)
            location = self.location.get(session)

            self.task.invoke(session,
                             scheduler,
                             description,
                             location,
                             attrs=attrs)

            self.task.exit_with_redirect(session, scheduler)

    class LocationField(StringField):
        def render_title(self, session):
            return "DAG file location"

standard_job_attributes = {
    "DiskUsage": 0,
    }

def log_job_ad(ad):
    log.debug("Job ad:")

    for item in sorted(ad.items()):
        log.debug("  %-34s  %r", *item)
