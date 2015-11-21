import logging

from wooly import Widget
from wooly.template import WidgetTemplate
from wooly.util import StringCatalog, Writer

from cumin.objectframe import ObjectFrame, ObjectView
from cumin.stat import StatFlashChart, StatSet
from cumin.grid.dashboard import PoolDashboard
from cumin.grid.tags import TagsNodeEditTask, TagsFrame, TagInventory

from submission import PoolSubmissionFrame, PoolSubmissionJoinSelector
from slot import SlotFrame
from scheduler import SchedulerFrame, SchedulerSelector
from negotiator import NegotiatorFrame, NegotiatorSelector,\
    NegotiatorEditDynamicQuota
from limit import LimitFrame, LimitSelector
from cumin.grid.quota import QuotaSelector 
from cumin.grid.slotvis import SlotOverview
from cumin.parameters import YoungestAttribute

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.pool")

class PoolView(ObjectView):
    def __init__(self, app, name, object):
        super(PoolView, self).__init__(app, name, object)

        self.error_tmpl = WidgetTemplate(self, "error_html")

    def do_render(self, session):
        id = self.frame.id.get(session)
        if not id:
            writer = Writer()
            self.error_tmpl.render(writer, session)
            return writer.to_string()

        return super(PoolView, self).do_render(session)

    def render_title(self, session):
        obj = self.object.get(session)
        if not obj:
            return "Missing Pool"

        return obj.get_title()

class PoolFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Collector

        # cls is used by ObjectFrames during the "process" pass 
        # to find self.id and self.object, the handle to an 
        # object in the db and the Rosemary representation of
        # the object itself.
        super(PoolFrame, self).__init__(app, name, cls)

        self.icon_href = "resource?name=pool-36.png"

        self.view = PoolView(app, "view", self.object)
        self.replace_child(self.view)

        self.mode.default = self.view

        self.submission = PoolSubmissionFrame(app, "submission")
        self.add_mode(self.submission)

        self.slot = SlotFrame(app, "slot")
        self.add_mode(self.slot)

        self.scheduler = SchedulerFrame(app, "scheduler")
        self.add_mode(self.scheduler)

        self.negotiator = NegotiatorFrame(app, "negotiator")
        self.add_mode(self.negotiator)

        self.limit = LimitFrame(app, "limit")
        self.add_mode(self.limit)
        
        self.tag = TagsFrame(app, "tag")
        self.add_mode(self.tag)
        self.tag.cumin_module = "configuration"

        dashboard = PoolDashboard(app, "dashboard", self.object)
        self.view.add_tab(dashboard)

        submissions = PoolSubmissionJoinSelector(app, "pool_submissions")
        self.view.add_tab(submissions)

        slots = SlotOverview(app, "slots")
        self.view.add_tab(slots)

        schedulers = SchedulerSelector(app, "schedulers")
        self.view.add_tab(schedulers)

        negotiators = NegotiatorSelector(app, "negotiators")
        self.view.add_tab(negotiators)

        cls = app.model.com_redhat_grid.Negotiator
        self.negotiator_attribute = YoungestAttribute(app, "neg", cls)
        self.add_attribute(self.negotiator_attribute)

        self.edit_dynamic_quota = NegotiatorEditDynamicQuota(app, self)
        self.quotas = QuotaSelector(app, "quotas", self.negotiator_attribute, self)
        self.view.add_tab(self.quotas)

        self.limits = LimitSelector(app, "limits")
        self.view.add_tab(self.limits)
        
        self.edit_node_tags = TagsNodeEditTask(app, self)
        config_editor = TagInventory(app, "tagi")
        self.view.add_tab(config_editor)

        self.top_tab = True

    def render_title(self, session):
        return "Grid"

    def get_title(self, session):
        obj = self.object.get(session)
        if not obj:
            return None

        return super(PoolFrame, self).get_title(session)

    def do_process(self, session):
        id = self.id.get(session)
        if not id:
            collector = self.app.model.find_youngest(self.cls, session.cursor)
            if collector:
                self.id.set(session, collector._id)
                id = collector._id

        # If we still don't have an id, skip the processing step.
        # This avoids an assertion error in do_process
        # When we go to render, we will get the "Missing Pool" banner
        # from PoolView, so the user will get a nice message
        if id:
            super(PoolFrame, self).do_process(session)

