from wooly import *
from wooly.forms import *
from wooly.resources import *
from wooly.tables import *
from wooly.widgets import *

from cumin.formats import *
from cumin.objectframe import *
from cumin.objectselector import *
from cumin.objecttask import *
from cumin.parameters import *
from cumin.sqladapter import *
from cumin.stat import *
from cumin.util import *
from cumin.widgets import *

from binding import *

from subscription import *

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.messaging.queue")

class QueueFrame(ObjectFrame):
    def __init__(self, app, name, vhost):
        cls = app.model.org_apache_qpid_broker.Queue

        super(QueueFrame, self).__init__(app, name, cls)

        self.icon_href = "resource?name=queue-36.png"

        self.overview = QueueOverview(app, "overview", self.object)
        self.view.add_tab(self.overview)

        self.bindings = QueueBindingSelector(app, "q_bindings", self.object)
        self.view.add_tab(self.bindings)

        self.subscriptions = SubscriptionSelector \
            (app, "subscriptions", self.object)
        self.view.add_tab(self.subscriptions)

        self.subscription = SubscriptionFrame(app, "subscription")
        self.add_mode(self.subscription)

        self.remove = QueueRemove(app, self)
        self.purge = QueuePurge(app, self)
        self.move_messages = MoveQueueMessages(app, self)
        self.add_binding = QueueBindingAdd(app, self)

class QueueRemove(ObjectFrameTask):
    def get_title(self, session):
        return "Remove"

    def do_exit(self, session):
        self.app.main_page.main.messaging.broker.view.show(session)

    def do_invoke(self, invoc, queue):
        session = self.app.model.get_session_by_object(queue)
        session.queue_delete(queue=queue.name)
        session.sync()

        invoc.end()

class QueueSelector(ObjectSelector):
    def __init__(self, app, name, vhost):
        cls = app.model.org_apache_qpid_broker.Queue

        super(QueueSelector, self).__init__(app, name, cls)

        self.vhost = vhost

        frame = "main.messaging.broker.queue"
        col = ObjectLinkColumn(app, "name", cls.name, cls._id, frame)
        self.add_column(col)
        self.add_search_filter(col)

        self.add_attribute_column(cls.consumerCount)
        self.add_attribute_column(cls.bindingCount)
        self.add_attribute_column(cls.msgDepth)
        self.add_attribute_column(cls.byteDepth)

        self.add_reference_filter(vhost, cls.vhostRef)

        self.remove = QueueSelectionRemove(app, self)
        self.purge = QueueSelectionPurge(app, self)

        self.enable_csv_export(vhost)

class QueueSelectionRemove(ObjectSelectorTask):
    def get_title(self, session):
        return "Remove"

    def do_invoke(self, invoc, queue):
        session = self.app.model.get_session_by_object(queue)
        session.queue_delete(queue=queue.name)
        session.sync()

        invoc.end()

class QueueSelectionPurge(ObjectSelectorTask):
    def get_title(self, session):
        return "Purge"

    def do_invoke(self, invoc, queue, count=0):        
        self.app.remote.qmf.purge_queue(queue, count, invoc.make_callback())

class QueueBindingSelector(BindingSelector):
    def __init__(self, app, name, queue):
        super(QueueBindingSelector, self).__init__(app, name)

        self.queue = queue

        self.add_reference_filter(self.queue, self.cls.queueRef)

        self.queue_column.visible = False

        self.enable_csv_export(queue)

class QueueAdd(ObjectFrameTask):
    def __init__(self, app, frame):
        super(QueueAdd, self).__init__(app, frame)

        self.form = QueueAddForm(app, self.name, self)

    def get_title(self, session):
        return "Add queue"

    def do_invoke(self, invoc, queue, name, durable, args):
        session = self.app.model.get_session_by_object(queue)
        session.queue_declare(queue=name, durable=durable, arguments=args)
        session.sync()

        invoc.end()

class QueueAddForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(QueueAddForm, self).__init__(app, name, task)

        self.namef = NameField(app, "name")
        self.add_field(self.namef)

        self.durable = self.QueueDurabilityField(app, "durable")
        self.add_extra_field(self.durable)

        self.cluster_durable = self.ClusterDurabilityField \
            (app, "cluster_durable")
        self.add_extra_field(self.cluster_durable)

        self.lvq = self.LVQField(app, "lvq")
        self.add_extra_field(self.lvq)

        self.optimistic = self.OptimisticField(app, "optimistic")
        self.add_extra_field(self.optimistic)

        self.file_count = self.FileCountField(app, "file_count")
        self.file_count.input.param.default = 8
        self.add_extra_field(self.file_count)

        self.file_size = self.FileSizeField(app, "file_size")
        self.file_size.input.param.default = 24
        self.add_extra_field(self.file_size)

        self.policy = self.PolicyField(app, "policy")
        self.add_extra_field(self.policy)

        self.q_size = self.QSizeField(app, "q_size")
        self.add_extra_field(self.q_size)

        self.q_count = self.QCountField(app, "q_count")
        self.add_extra_field(self.q_count)

    class AdvancedOptions(MoreFieldSet):
        def render_title(self, session):
            return "Advanced Options"

    class QCountField(IntegerField):
        def render_title(self, session):
            return "Max Queue Count"

        def render_field_help(self, session):
            return "(Maximum in-memory queue size as a number of messages. Applies if Policy is set.)"

    class QSizeField(IntegerField):
        def render_title(self, session):
            return "Max Queue Size"

        def render_field_help(self, session):
            return "(Maximum in-memory queue size as bytes. Applies if Policy is set.)"

    class FileCountField(IntegerField):
        def render_title(self, session):
            return "File Count"

        def render_field_help(self, session):
            return "(Number of files in queue's persistence journal)"

    class FileSizeField(IntegerField):
        def render_title(self, session):
            return "File Size"

        def render_field_help(self, session):
            return "(File size in pages - 64Kb/page)"

    class QueueDurabilityField(TwoOptionRadioField):
        def render_title(self, session):
            return "Durable?"

        def render_field_help(self, session):
            return "(Queue is durable)"

        def render_title_1(self, session):
            return "Durable"

        def render_title_2(self, session):
            return "Transient"

    class ClusterDurabilityField(TwoOptionRadioField):
        def render_title(self, session):
            return "Cluster Durable?"

        def render_field_help(self, session):
            return "(Queue becomes durable if there is only one functioning cluster node)"

        def render_title_1(self, session):
            return "Cluster Durable"

        def render_title_2(self, session):
            return "Not Cluster Durable"

    class LVQField(TwoOptionRadioField):
        def render_title(self, session):
            return "Enable Last Value Queue?"

        def render_field_help(self, session):
            return "(Enable LVQ behavior on the queue)"

        def render_title_1(self, session):
            return "Enabled"

        def render_title_2(self, session):
            return "Not Enabled"

    class OptimisticField(TwoOptionRadioField):
        def render_title(self, session):
            return "Enable Optimistic Consume?"

        def render_field_help(self, session):
            return "(Enable optimistic consume on the queue)"

        def render_title_1(self, session):
            return "Enabled"

        def render_title_2(self, session):
            return "Not Enabled"

    class PolicyField(RadioField):
        def __init__(self, app, name):
            super(QueueAddForm.PolicyField, self).__init__(app, name, None)

            self.param = Parameter(app, "param")
            self.param.default = "none"
            self.add_parameter(self.param)

            option = self.NoneField(app, "none", self.param)
            self.add_option(option)

            option = self.Reject(app, "reject", self.param)
            self.add_option(option)

            option = self.Flow(app, "flow", self.param)
            self.add_option(option)

            option = self.Ring(app, "ring", self.param)
            self.add_option(option)

            option = self.RingStrict(app, "ring_strict", self.param)
            self.add_option(option)

        def render_title(self, session):
            return "Policy-type"

        def render_field_help(self, session):
            return "(Action taken when queue limit is reached)"

        class NoneField(RadioFieldOption):
            def render_value(self, session):
                return "none"

            def render_title(self, session):
                return "None"

        class Reject(RadioFieldOption):
            def render_value(self, session):
                return "reject"

            def render_title(self, session):
                return "Reject"

        class Flow(RadioFieldOption):
            def render_value(self, session):
                return "flow"

            def render_title(self, session):
                return "Flow to disc"

        class Ring(RadioFieldOption):
            def render_value(self, session):
                return "ring"

            def render_title(self, session):
                return "Ring"

        class RingStrict(RadioFieldOption):
            def render_value(self, session):
                return "ring_strict"

            def render_title(self, session):
                return "Ring Strict"

    def process_submit(self, session):
        vhost = self.object.get(session)

        name = self.namef.get(session)
        durable = self.durable.get(session)
        policy = self.policy.get(session)

        self.validate(session)

        errors = self.errors.get(session)
        if not errors:
            args = dict()

            if durable:
                args["qpid.file_count"] = self.file_count.get(session)
                args["qpid.file_size"] = self.file_size.get(session)

            if policy != "none":
                args["qpid.policy_type"] = policy
                args["qpid.max_size"] = self.q_size.get(session)
                args["qpid.max_count"] = self.q_count.get(session)

            args["qpid.persist_last_node"] = \
                self.cluster_durable.get(session) == "yes"

            args["qpid.last_value_queue"] = \
                self.lvq.get(session) == "enable"

            args["qpid.optimistic_consume"] = \
                self.optimistic.get(session) == "yes"

            self.task.invoke(session, vhost, name, durable, args)
            self.task.exit_with_redirect(session)

class QueuePurge(ObjectFrameTask):
    def __init__(self, app, frame):
        super(QueuePurge, self).__init__(app, frame)

        self.form = QueuePurgeForm(app, self.name, self)

    def get_title(self, session):
        return "Purge"

    def do_invoke(self, invoc, queue, count=0):
        self.app.remote.qmf.purge_queue(queue, count, invoc.make_callback())

class QueuePurgeForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(QueuePurgeForm, self).__init__(app, name, task)

        self.purge_request = MultiplicityField(app, "purge_request")
        self.add_field(self.purge_request)

    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            queue = self.object.get(session)

            request_amt = self.purge_request.get(session)

            if request_amt == "all":
                count = 0
            elif request_amt == "top":
                count = 1
            elif request_amt == "N":
                count = self.purge_request.top_n.get_n_value(session)
            else:
                raise Exception("Wrong Value")

            self.task.invoke(session, queue, count)
            self.task.exit_with_redirect(session)

class QueueBindingAdd(BindingAddTask):
    def __init__(self, app, frame):
        super(QueueBindingAdd, self).__init__(app, frame)

        self.form = QueueBindingAddForm(app, self.name, self)

class QueueBindingAddForm(BindingAddForm):
    def __init__(self, app, name, task):
        super(QueueBindingAddForm, self).__init__(app, name, task)

        self.q_field.input.disabled = True

class QueueOverview(RadioModeSet):
    def __init__(self, app, name, queue):
        super(QueueOverview, self).__init__(app, name)

        self.add_tab(QueueStatsGeneral(app, "gen", queue))
        self.add_tab(QueueStatsDurability(app, "dur", queue))
        self.add_tab(QueueStatsTransactions(app, "txn", queue))

    def render_title(self, session):
        return "Overview"

class QueueGeneralStatSet(StatSet):
    def __init__(self, app, name, object):
        super(QueueGeneralStatSet, self).__init__(app, name, object)

        self.attrs = ("consumerCount", "bindingCount",
                           "msgDepth", "byteDepth")

class QueueIOStatSet(StatSet):
    def __init__(self, app, name, object):
        super(QueueIOStatSet, self).__init__(app, name, object)

        self.attrs = ("msgTotalEnqueues", "msgTotalDequeues",
                           "byteTotalEnqueues", "byteTotalDequeues",
                           "unackedMessages", "messageLatency")

class QueueStatsGeneral(Widget):
    def __init__(self, app, name, queue):
        super(QueueStatsGeneral, self).__init__(app, name)

        self.add_child(QueueGeneralStatSet(app, "general", queue))
        self.add_child(QueueIOStatSet(app, "io", queue))

        chart = self.EnqueueDequeueRateChart(app, "enqdeq", queue)
        chart.stats = ("msgTotalEnqueues", "msgTotalDequeues")
        chart.mode = "rate"
        self.add_child(chart)

        chart = self.DepthChart(app, "depth", queue)
        chart.stats = ("msgDepth",)
        self.add_child(chart)

        chart = StatFlashChart(app, "consumers", queue)
        chart.stats = ("consumerCount",)
        self.add_child(chart)

    def render_title(self, session):
        return "General"

    class EnqueueDequeueRateChart(StatFlashChart):
        def render_title(self, session):
            return "Messages enqueued and dequeued"

    class DepthChart(StatFlashChart):
        def render_title(self, session):
            return "Queue Depth"

class QueueIODurableStatSet(StatSet):
    def __init__(self, app, name, object):
        super(QueueIODurableStatSet, self).__init__(app, name, object)

        self.attrs = ("msgPersistEnqueues", "msgPersistDequeues",
                           "bytePersistEnqueues", "bytePersistDequeues")

class QueueStatsDurability(Widget):
    def __init__(self, app, name, queue):
        super(QueueStatsDurability, self).__init__(app, name)

        self.add_child(QueueIODurableStatSet(app, "io", queue))
        self.add_child(JournalStats(app, "jrnl", queue))

        chart = self.EnqueueDequeueRateChart(app, "enqdeq", queue)
        chart.stats = ("msgPersistEnqueues", "msgPersistDequeues")
        chart.mode = "rate"
        self.add_child(chart)

    def render_title(self, session):
        return "Durability"

    class EnqueueDequeueRateChart(StatFlashChart):
        def render_title(self, session):
            return "Durable messages enqueued and dequeued"

class JournalStats(StatSet):
    def __init__(self, app, name, queue):
        super(JournalStats, self).__init__(app, name, queue)

        self.journal = self.JournalAttribute(app, "journal")
        self.add_attribute(self.journal)

        self.attrs = ("initialFileCount", "dataFileSize",
                       "recordDepth", "recordEnqueues",
                       "outstandingAIOs", "freeFileCount",
                       "availableFileCount", "writeWaitFailures",
                       "writeBusyFailures", "readRecordCount",
                       "readBusyFailures", "writePageCacheDepth",
                       "readPageCacheDepth")

    class JournalAttribute(Attribute):
        def get(self, session):
            queue = self.widget.object.get(session)
            cls = self.app.model.com_redhat_rhm_store.Journal

            journals = cls.get_selection(session.cursor,
                                         _queueRef_id=queue._id)

            return len(journals)

    def render_title(self, session):
        return "Journal"

    def do_render(self, session):
        journal = self.journal.get(session)

        if journal:
            return super(JournalStats, self).do_render(session)
        else:
            return "<div class=\"iblock\">%s</div>" % fmt_none()

class QueueTxnStatSet(StatSet):
    def __init__(self, app, name, queue):
        super(QueueTxnStatSet, self).__init__(app, name, queue)

        self.attrs = ("msgTxnEnqueues", "msgTxnDequeues",
                       "byteTxnEnqueues", "byteTxnDequeues")

class QueueStatsTransactions(Widget):
    def __init__(self, app, name, queue):
        super(QueueStatsTransactions, self).__init__(app, name)

        self.add_child(QueueTxnStatSet(app, "io", queue))

        chart = self.EnqueueDequeueRateChart(app, "enqdeq", queue)
        chart.stats = ("msgTxnEnqueues", "msgTxnDequeues")
        chart.mode = "rate"
        self.add_child(chart)

    def render_title(self, session):
        return "Transactions"

    class EnqueueTransactionRateChart(StatFlashChart):
        def render_title(self, session):
            return "Enqueue transaction operations per second"

    class DequeueTransactionRateChart(StatFlashChart):
        def render_title(self, session):
            return "Dequeue transaction operations per second"

    class EnqueueDequeueRateChart(StatFlashChart):
        def render_title(self, session):
            return "Transactional messages enqueued and dequeued"

class QueueSelectField(FormField):
    def __init__(self, app, name, form, param):
        super(QueueSelectField, self).__init__(app, name)

        self.org_param = param
        self.param = self.QueueSearchInputSet(app, "queue_set", param)
        self.add_child(self.param)

    def get(self, session):
        return self.org_param.get(session)

    def render_title(self, session):
        return "Queue"

    def render_inputs(self, session):
        return self.param.render(session)

    def validate(self, session):
        if self.required:
            val = self.get(session)
            if not val:
                error = FormError("The %s is required" % self.render_title(session))
                self.form.errors.add(session, error)

    class QueueSearchInputSet(IncrementalSearchInput):
        def do_get_items(self, session):
            cls = self.app.model.org_apache_qpid_broker.Queue
            vhost = self.form.get_object(session)
            vhostid = vhost._id
            queues = cls.get_selection(session.cursor, _vhostRef_id=vhostid)
            queue_list_full = sorted_by(list(queues))
            delta = timedelta(days=3)
            queue_list = []
            for _queue in queue_list_full:
                if _queue._qmf_update_time > (datetime.now() - delta):
                    queue_list.append(_queue)
            return queue_list

        def render_item_content(self, session, queue):
            return xml_escape(queue.name) or "<em>Default</em>"

        def render_item_value(self, session, queue):
            return queue._id

class MoveMessagesBase(ObjectFrameTask):
    def get_title(self, session):
        return "Move messages"

    def do_invoke(self, invoc, vhost, src, dst, count):
        cursor = self.app.database.get_read_cursor()

        cls = self.app.model.org_apache_qpid_broker.Broker
        broker = cls.get_object_by_id(cursor, vhost._brokerRef_id)
        self.app.remote.qmf.queue_move_messages(broker, src, dst, count, invoc.make_callback())

class MoveQueueMessages(MoveMessagesBase):
    def __init__(self, app, frame):
        super(MoveQueueMessages, self).__init__(app, frame)

        self.form = MoveQueueMessagesForm(app, self.name, self)

class MoveMessages(MoveMessagesBase):
    def __init__(self, app, frame):
        super(MoveMessages, self).__init__(app, frame)

        self.form = MoveMessagesForm(app, self.name, self)

class MoveMessagesFormBase(ObjectFrameTaskForm):
    def __init__(self, app, name, task, src_queue):
        super(MoveMessagesFormBase, self).__init__(app, name, task)

        self.src_queue = src_queue
        self.add_field(src_queue)

        self.dqueue = StringParameter(app, "dqueue")
        self.add_parameter(self.dqueue)
        self.dest_queue = self.QueueDestField(app, "dest", self, self.dqueue)
        self.dest_queue.required = True
        self.add_field(self.dest_queue)

        self.count = MultiplicityField(app, "count")
        self.add_field(self.count)

    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            src_queue = self.src_queue.get(session)
            dest_queue = self.dest_queue.get(session)
            object = self.get_object(session)
            scount = self.count.get(session)

            if scount == "all":
                count = 0
            elif scount == "top":
                count = 1
            elif scount == "N":
                count = self.count.top_n.get_n_value(session)
            else:
                raise Exception("Wrong Value")

            self.task.invoke(session, object, src_queue, dest_queue, count)
            self.task.exit_with_redirect(session)

    def get_object(self, session):
        return self.object.get(session)

    class QueueDestField(QueueSelectField):
        def render_title(self, session):
            return "Destination Queue"

class MoveMessagesForm(MoveMessagesFormBase):
    def __init__(self, app, name, task):
        self.squeue = StringParameter(app, "queue")
        src_queue = self.QueueSrctField(app, "src", self, self.squeue)
        src_queue.required = True
        super(MoveMessagesForm, self).__init__(app, name, task, src_queue)
        self.add_parameter(self.squeue)

    class QueueSrctField(QueueSelectField):
        def render_title(self, session):
            return "Source Queue"

class MoveQueueMessagesForm(MoveMessagesFormBase):
    def __init__(self, app, name, task):
        src_queue = self.QueueSrcField(app, "src")
        super(MoveQueueMessagesForm, self).__init__(app, name, task, src_queue)

    def get_object(self, session):
        # task expects a vhost object
        queue = self.object.get(session)
        cls = self.app.model.org_apache_qpid_broker.Vhost
        vhost = cls.get_object_by_id(session.cursor, queue._vhostRef_id)
        return vhost

    class QueueSrcField(FormField):
        def render_title(self, session):
            return "Source Queue"

        def render_inputs(self, session):
            return xml_escape(self.get(session))

        def get(self, session):
            queue = self.form.object.get(session)
            return queue.name
