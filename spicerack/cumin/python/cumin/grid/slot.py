import logging

from wooly.widgets import *
from wooly.forms import *
from wooly.resources import *
from wooly.tables import *

from cumin.objectframe import *
from cumin.objectselector import *
from cumin.stat import *
from cumin.widgets import *
from cumin.OpenFlashChart import *

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.slot")

class SlotFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Slot

        super(SlotFrame, self).__init__(app, name, cls)

class SlotLoadStatSet(StatSet):
    def __init__(self, app, name, object):
        super(SlotLoadStatSet, self).__init__(app, name, object)

        self.attrs = ("CondorLoadAvg", "LoadAvg"),

class SlotStats(Widget):
    def __init__(self, app, name, slot):
        super(SlotStats, self).__init__(app, name)

        stats = SlotLoadStatSet(app, "general", slot)
        self.add_child(stats)

        job_info = SlotJobInfo(app, "job_info", slot, "JobInfo")
        self.add_child(job_info)

        chart = self.LoadChart(app, "chart", slot)
        chart.stats = ("LoadAvg", "CondorLoadAvg")
        chart.duration.param.default = "3600"
        self.add_child(chart)

    def render_title(self, session):
        return "Statistics"

    class LoadChart(StatFlashChart):
        def render_title(self, session):
            return "Load"

class SlotJobInfo(PropertySet):
    def __init__(self, app, name, slot, category):
        super(SlotJobInfo, self).__init__(app, name)

        #self.defer_enabled = True
        self.update_enabled = True
        self.category = category
        self.object = slot

    def do_get_items(self, session):
        obj = self.object.get(session)
        cls = self.app.model.get_class_by_object(obj)

        return [(x.get_title(session), x.value(session, obj), x.escape)
                for x in cls.properties if x.category == self.category]

