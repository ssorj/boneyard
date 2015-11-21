import logging

from wooly import *
from wooly.widgets import *
from wooly.forms import *
from wooly.resources import *
from wooly.tables import *

from cumin.objectframe import *
from cumin.objectselector import *
from cumin.stat import *
from cumin.widgets import *
from cumin.parameters import *
from cumin.formats import *
from cumin.util import *

from submission import *

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.grid.submitter")

class SubmitterFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Submitter

        super(SubmitterFrame, self).__init__(app, name, cls)

        overview = SubmitterOverview(app, "overview", self.object)
        self.view.add_tab(overview)

        # submissions XXX

class SubmitterSelector(ObjectSelector):
    def __init__(self, app, name, scheduler):
        cls = app.model.com_redhat_grid.Submitter

        super(SubmitterSelector, self).__init__(app, name, cls)

        self.scheduler = scheduler

        self.add_reference_filter(self.scheduler, cls.schedulerRef)

        frame = "main.grid.scheduler.submitter"
        col = ObjectLinkColumn(app, "name", cls.Name, cls._id, frame)
        self.add_column(col)
        self.add_search_filter(col)

        self.add_attribute_column(cls.Machine)
        self.add_attribute_column(cls.ScheddName)
        self.add_attribute_column(cls.IdleJobs)
        self.add_attribute_column(cls.RunningJobs)
        self.add_attribute_column(cls.HeldJobs)

        self.enable_csv_export(scheduler)

class SubmitterGeneralStatSet(StatSet):
    def __init__(self, app, name, object):
        super(SubmitterGeneralStatSet, self).__init__(app, name, object)

        self.attrs = ("RunningJobs", "IdleJobs", "HeldJobs")

class SubmitterOverview(Widget):
    def __init__(self, app, name, submitter):
        super(SubmitterOverview, self).__init__(app, name)

        stats = SubmitterGeneralStatSet(app, "general", submitter)
        self.add_child(stats)

        chart = self.JobsChart(app, "jobs", submitter)
        chart.stats = ("RunningJobs", "IdleJobs", "HeldJobs")
        self.add_child(chart)

    def render_title(self, session):
        return "Overview"

    class JobsChart(StatFlashChart):
        def render_title(self, session):
            return "Jobs"
