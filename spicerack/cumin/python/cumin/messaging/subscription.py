from cumin.objectframe import *
from cumin.objectselector import *
from cumin.stat import *
from cumin.util import *

strings = StringCatalog(__file__)

class SubscriptionSelector(ObjectSelector):
    def __init__(self, app, name, queue):
        cls = app.model.org_apache_qpid_broker.Subscription

        super(SubscriptionSelector, self).__init__(app, name, cls)

        self.queue = queue

        frame = "main.messaging.broker.queue.subscription"
        col = ObjectLinkColumn(app, "name", cls.name, cls._id, frame)
        self.add_column(col)
        self.add_search_filter(col)

        self.add_attribute_column(cls.creditMode)
        self.add_attribute_column(cls.arguments)
        self.add_attribute_column(cls.delivered)

        self.enable_csv_export(queue)

class SubscriptionFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.org_apache_qpid_broker.Subscription

        super(SubscriptionFrame, self).__init__(app, name, cls)

        overview = SubscriptionStats(app, "overview", self.object)
        self.view.add_tab(overview)

class SubscriptionStats(Widget):
    def __init__(self, app, name, subscription):
        super(SubscriptionStats, self).__init__(app, name)

        stats = StatSet(app, "stats", subscription)
        stats.attrs = ("delivered",)
        self.add_child(stats)

        chart = StatFlashChart(app, "delivered", subscription)
        chart.stats = ("delivered",)
        self.add_child(chart)

    def render_title(self, session):
        return "Overview"
