import logging

from wooly import Widget
from wooly.util import StringCatalog
from wooly.widgets import RadioModeSet, WidgetSet

from cumin.stat import *
from cumin.objectframe import ObjectFrame
from submitter import SubmitterFrame, SubmitterSelector
from submission import PoolSubmissionSelector
from cumin.objectselector import ObjectSelectorTable, ObjectSelector,\
    ObjectLinkColumn, MonitorSelfStatColumn, ObjectTable, MonitorSelfAgeColumn, SelectableSearchObjectTable
from cumin.grid.submission import SubmissionFrame

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.grid.scheduler")

class SchedulerFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Scheduler

        super(SchedulerFrame, self).__init__(app, name, cls)

        self.submitter = SubmitterFrame(app, "submitter")
        self.add_mode(self.submitter)
        
        self.submission = SubmissionFrame(app, "submission")
        self.add_mode(self.submission)        

        overview = SchedulerOverview(app, "overview", self.object)
        self.view.add_tab(overview)

        submissions = SchedulerPoolSubmissionSelector(app, "submissions", self.object)
        self.view.add_tab(submissions)

        submitters = SubmitterSelector(app, "submitters", self.object)
        self.view.add_tab(submitters)

        #self.start = DaemonStart(app, self, "SCHEDD")
        #self.stop = DaemonStop(app, self, "SCHEDD")

class SchedulerPoolSubmissionSelector(PoolSubmissionSelector):
    def __init__(self, app, name, scheduler):
        frame = "main.grid.scheduler.submission"
        super(SchedulerPoolSubmissionSelector, self).__init__(app, name, frame)

        self.add_reference_filter(scheduler, self.cls.jobserverRef)
        self.enable_csv_export(scheduler)

    def create_table(self, app, name, cls):
        return self.JoinTable(app, name, cls)

    class JoinTable(ObjectTable):
        def get_data_values(self, session):
            values = super(SchedulerPoolSubmissionSelector.JoinTable, self).get_data_values(session)

            jobserver_key = self.cls.jobserverRef.name

            # could also use self.frame.id.get(session)
            scheduler_id = values[jobserver_key]

            #we need to find the _id of the jobServer whose _schedulerRef_id matches our scheduler
            cls = self.app.model.com_redhat_grid.JobServer
            job_server = cls.get_object(session.cursor, _schedulerRef_id=scheduler_id)

            # Awkward: if there is no jobserver for this scheduler, don't select any records.
            # An alternative is to create our own adapter and override the get_data method
            jobserver_id = job_server and job_server._id or -1

            values[jobserver_key] = jobserver_id
            return values

class SchedulerSelector(ObjectSelector):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Scheduler

        super(SchedulerSelector, self).__init__(app, name, cls)

        frame = "main.grid.scheduler"
        col = ObjectLinkColumn(app, "name", cls.Name, cls._id, frame)
        self.add_column(col)

        self.add_attribute_column(cls.NumUsers)
        self.add_attribute_column(cls.TotalIdleJobs)
        self.add_attribute_column(cls.TotalRunningJobs)
        self.add_attribute_column(cls.TotalHeldJobs)
        
        self.field_param = StringParameter(app, "field_param")
        self.add_parameter(self.field_param)
        
        self.select_input = self.SchedulerFieldOptions(app, self.field_param)
        self.add_selectable_search_filter(self.select_input)

        stat = MonitorSelfAgeColumn(app, cls.MonitorSelfAge.name, cls.MonitorSelfAge)
        self.add_column(stat)
        stat = MonitorSelfStatColumn(app, cls.MonitorSelfCPUUsage.name, cls.MonitorSelfCPUUsage)
        self.add_column(stat)
        stat = MonitorSelfStatColumn(app, cls.MonitorSelfImageSize.name, cls.MonitorSelfImageSize)
        self.add_column(stat)

        #self.start = DaemonSelectionStart(app, self, "SCHEDD")
        #self.stop = DaemonSelectionStop(app, self, "SCHEDD")

        self.enable_csv_export()

    def create_table(self, app, name, cls):
        # avoid the checkboxes
        return SelectableSearchObjectTable(app, name, cls)
    
    class SchedulerFieldOptions(SelectableSearchObjectTable.SearchFieldOptions):
        def __init__(self, app, param):
            super(SchedulerSelector.SchedulerFieldOptions, self).__init__(app, param)
            self.cls = app.model.com_redhat_grid.Scheduler
            
        def do_get_items(self, session):
            return [self.cls.Name, self.cls.NumUsers, self.cls.TotalIdleJobs, \
                    self.cls.TotalRunningJobs, self.cls.TotalHeldJobs, self.cls.MonitorSelfAge, \
                    self.cls.MonitorSelfCPUUsage, self.cls.MonitorSelfImageSize]

class SchedulerOverview(RadioModeSet):
    def __init__(self, app, name, scheduler):
        super(SchedulerOverview, self).__init__(app, name)

        self.add_tab(SchedulerOverviewGeneral(app, "general", scheduler))
        self.add_tab(SchedulerOverviewCycle(app, "cycle", scheduler))

    def render_title(self, session):
        return "Overview"

class SchedulerGeneralStatSet(StatSet):
    def __init__(self, app, name, object):
        super(SchedulerGeneralStatSet, self).__init__(app, name, object)

        self.attrs = ("NumUsers", "TotalRunningJobs",
                      "TotalIdleJobs", "TotalHeldJobs",
                      "TotalJobAds", "TotalRemovedJobs",
                      "MonitorSelfAge", "MonitorSelfCPUUsage",
                      "MonitorSelfImageSize","MonitorSelfRegisteredSocketCount",
                      "MonitorSelfResidentSetSize","MonitorSelfTime")
        
    def render_formatted_value(self, session, item, value, escape=False):
        def fmt_b(value):
            return value is not None and fmt_bytes(value) or None

        def fmt_kb(value):
            return value is not None and fmt_bytes(value * 1024) or None

        def fmt_mb(value):
            return value is not None and fmt_bytes(value * 1024 * 1024) or None
        
        def fmt_timestamp_ddhhmmss(value):
            days = value / 86400
            hours = (value / 3600) - (days * 24)
            minutes = (value / 60) - (days * 1440) - (hours * 60)
            return '%02d:%02d:%02d' % (days, hours, minutes)

        try:
            format = self.get_item_unit(session, item)
            if format:
                if format == "MiB":
                    return fmt_mb(value)
                elif format == "KiB":
                    return fmt_kb(value)
            name = self.get_item_name(session, item)
            # Since condor.xml doesn't have a unit for this, we improvise a bit.
            # This could perhaps use the same Rosemary code as Negotiator.
            if(name in ["MonitorSelfAge"]):
                return fmt_timestamp_ddhhmmss(value)
        except:
            pass

        return CuminStatistic.fmt_value(value, escape)
    
    def get_item_name(self, session, item):
        the_item, _ = item
        return the_item.name

class SchedulerOverviewGeneral(Widget):
    def __init__(self, app, name, scheduler):
        super(SchedulerOverviewGeneral, self).__init__(app, name)

        stats = SchedulerGeneralStatSet(app, "general", scheduler)
        self.add_child(stats)

        chart = self.UsersChart(app, "users", scheduler)
        chart.stats = ("NumUsers",)
        chart.duration.param.default = "3600"
        self.add_child(chart)

        chart = self.JobsChart(app, "jobs", scheduler)
        chart.stats = ("TotalRunningJobs", "TotalIdleJobs", "TotalHeldJobs")
        chart.duration.param.default = "3600"
        self.add_child(chart)

    def render_title(self, session):
        return "General stats"

    class UsersChart(StatFlashChart):
        def render_title(self, session):
            return "Users"

    class JobsChart(StatFlashChart):
        def render_title(self, session):
            return "Jobs"

class SchedulerOverviewCycle(Widget):
    def __init__(self, app, name, scheduler):
        super(SchedulerOverviewCycle, self).__init__(app, name)

        charts = WidgetSet(app, "charts")
        self.add_child(charts)

        chart = StatFlashChart(app, "started", scheduler)
        chart.title = "Job rates"
        chart.stats = ("JobSubmissionRate", "JobStartRate", "JobCompletionRate")
        chart.duration.param.default = "3600"
        charts.add_child(chart)

        chart = StatFlashChart(app, "submitted", scheduler)
        chart.title = "Job totals"
        chart.duration.param.default = "3600"
        chart.stats = ("JobsSubmitted", "JobsStarted", "JobsCompleted")
        charts.add_child(chart)

        chart = StatFlashChart(app, "exited", scheduler)
        chart.title = "Jobs exited/Shadow exceptions"
        chart.stats = ("JobsExited", "ShadowExceptions")
        chart.duration.param.default = "3600"
        charts.add_child(chart)

        chart = StatFlashChart(app, "exception", scheduler)
        chart.title = "Jobs exited/Shadow exceptions cumulative"
        chart.stats = ("JobsExitedCum", "ShadowExceptionsCum")
        chart.duration.param.default = "3600"
        charts.add_child(chart)

        chart = StatFlashChart(app, "start_time", scheduler)
        chart.title = "Mean times"
        chart.stats = ("MeanTimeToStart", "MeanRunningTime")
        chart.duration.param.default = "3600"
        charts.add_child(chart)

        chart = StatFlashChart(app, "running_time", scheduler)
        chart.title = "Mean times cumulative"
        chart.stats = ("MeanTimeToStartCum", "MeanRunningTimeCum")
        chart.duration.param.default = "3600"
        charts.add_child(chart)

        chart = StatFlashChart(app, "completed", scheduler)
        chart.title = "Cumulative jobs"
        chart.stats = ("JobsSubmittedCum", "JobsStartedCum", "JobsCompletedCum")
        chart.duration.param.default = "3600"
        charts.add_child(chart)

    def render_title(self, session):
        return "Performance"

    def render_statswindow(self, session):
        # get the average WindowedStarWidth for all schedulers
        statswindow = self.frame.object.get(session).WindowedStatWidth
        return statswindow
