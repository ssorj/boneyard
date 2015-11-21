from cumin.test import *
from cumin.util import *

import main

log = logging.getLogger("cumin.messaging.test")

class MessagingTest(Test):
    def __init__(self, name, parent):
        super(MessagingTest, self).__init__(name, parent)

        BrokerGroupTest("BrokerGroup", self, main.module.broker_group_add)

class BrokerGroupTest(TaskFormTest):
    def __init__(self, name, parent, task):
        super(BrokerGroupTest, self).__init__(name, parent, task)

        self.group = None

        self.Edit("edit", self, main.module.broker_group_edit)
        self.Remove("remove", self, main.module.broker_group_remove)

    def add_input(self, session, s):
        self.task.form.group_name.set(s, session.id)

    def check(self, session, s):
        self.group = check_get_object(BrokerGroup, name=session.id)

    class Edit(TaskFormTest):
        def enter(self, session, s):
            return self.task.enter(s, self.parent.group)

        def add_input(self, session, s):
            name = self.task.form.group_name.get(s)
            
            self.altered_name = name + "%;&#\\"

            self.task.form.group_name.set(s, self.altered_name)

        def check(self, session, s):
            assert self.parent.group.name == self.altered_name

    class Remove(TaskFormTest):
        def enter(self, session, s):
            return self.task.enter(s, self.parent.group)

        def check(self, session, s):
            check_removed(BrokerGroup, id=self.parent.group.id)

# XXX The tests below are as yet unconverted

class BrokerLinkTest(Test):
    def __init__(self, harness, parent):
        super(BrokerLinkTest, self).__init__(harness, parent)

        RouteTest(harness, self)
        self.LinkRemove(harness, self)

    def do_run(self, session):
        p, s = self.harness.page_and_session()

        p.main.broker.set_object(s, self.harness.broker)

        form = p.main.broker.link_add
        form.show(s)

        form.host.set(s, "localhost")
        form.port.set(s, "9991")
        form.submit(s)

        p.process(s)

        self.harness.check_redirect(p, s)

        vhost = self.harness.vhost

        def predicate():
            for item in Link.selectBy(vhost=vhost, host="localhost", port=9991):
                self.harness.link = item
                return True

        wait(predicate)

        self.run_children(session)

    class LinkRemove(Test):
        def do_run(self, session):
            p, s = self.harness.page_and_session()

            p.main.broker.set_object(s, self.harness.broker)

            form = p.main.broker.links_close
            form.show(s)
            form.ids.set(s, [self.harness.link.id])
            form.submit(s)

            p.process(s)

            self.harness.check_redirect(p, s)

            def predicate():
                return self.harness.link.qmfDeleteTime

            wait(predicate)

class RouteTest(Test):
    def __init__(self, harness, parent):
        super(RouteTest, self).__init__(harness, parent)

        self.Add(harness, self)
        self.Remove(harness, self)

    def do_run(self, session):
        self.run_children(session)

    class Add(Test):
        def do_run(self, session):
            p, s = self.harness.page_and_session()

            p.main.broker.set_object(s, self.harness.broker)
            p.main.broker.link.set_object(s, self.harness.link)

            form = p.main.broker.link.bridge_add
            form.show(s)

            vhost = self.harness.vhost
            exchange = Exchange.selectBy \
                (vhost=vhost, name=self.harness.broker_exchange.name)[0]
            form.exchange.set(s, str(exchange.id))

            form.key.set(s, "cumin.key")
            form.tag.set(s, "cumin.tag")
            form.excludes.set(s, "cumin.tag")

            form.submit(s)

            p.process(s)

            self.harness.check_redirect(p, s)

            def predicate():
                for item in Bridge.selectBy \
                        (link=self.harness.link,
                         dest=self.harness.broker_exchange.name,
                         key="cumin.key"):
                    self.harness.bridge = item
                    return True

            wait(predicate)

    class Remove(Test):
        def do_run(self, session):
            p, s = self.harness.page_and_session()

            p.main.broker.set_object(s, self.harness.broker)
            p.main.broker.link.set_object(s, self.evn.link)

            form = p.main.broker.link.routes_close
            form.show(s)
            form.ids.set(s, [self.harness.bridge.id])
            form.submit(s)

            p.process(s)

            self.harness.check_redirect(p, s)

            def predicate():
                return self.harness.bridge.qmfDeleteTime

            wait(predicate)

class BrokerTest(Test):
    def __init__(self, harness, parent):
        super(BrokerTest, self).__init__(harness, parent)

        VhostTest(harness, self)

    def do_run(self, session):
        try:
            sleep(10)
            self.harness.broker = Broker.select()[0]
        except IndexError:
            raise Exception("Broker not found")

        self.run_children(session)

class VhostTest(Test):
    def __init__(self, harness, parent):
        super(VhostTest, self).__init__(harness, parent)

        QueueTest(harness, self)
        ExchangeTest(harness, self)
        ConnectionTest(harness, self)
        BrokerLinkTest(harness, self)

    def do_run(self, session):
        def predicate():
            for item in Vhost.selectBy(broker=self.harness.broker, name="/"):
                return True

        wait(predicate)

        try:
            self.harness.vhost = Vhost.selectBy \
                (broker=self.harness.broker, name="/")[0]
        except IndexError:
            raise Exception("Vhost not found")

        self.run_children(session)

class BindQueueTest(Test):
    def __init__(self, harness, parent):
        super(BindQueueTest, self).__init__(harness, parent)

        self.BindDirect(harness, self)
        self.BindTopic(harness, self)
        self.BindFanout(harness, self)
        self.BindHeaders(harness, self)

    def do_run(self, session):
        self.run_children(session)

    class BindDirect(Test):
        def __init__(self, harness, parent):
            super(BindQueueTest.BindDirect, self).__init__(harness, parent)

            self.RemoveBindDirect(harness, self)

        def do_run(self, session):
            p, s = self.harness.page_and_session()

            p.main.broker.set_object(s, self.harness.broker.registration)
            p.main.broker.queue.set_object(s, self.harness.queue)

            form = p.main.broker.queue.binding_add
            form.show(s)

            binding = dict()
            binding["test"] = {}
            direct = binding["test"]
            direct["name"] = "amq.direct"
            direct["type"] = "direct"
            direct["key"] = "amq.direct.key"

            form.bindings.dict_param.set(s, binding)

            form.submit(s)

            p.process(s)

            self.harness.check_redirect(p, s)

            def predicate():
                for item in Binding.selectBy(queue=self.harness.queue, bindingKey=self.harness.queue.name):
                    self.harness.binding_direct = item
                    return True

            wait(predicate)

        class RemoveBindDirect(Test):
            def do_run(self, session):
                p, s = self.harness.page_and_session()

                p.main.broker.set_object(s, self.harness.broker)

                form = p.main.broker.bindings_remove.show(s)
                form.ids.set([self.harness.binding_direct.id])
                form.submit(s)

                p.process(s)

                self.harness.check_redirect(p, s)

                def predicate():
                    return self.harness.binding_direct.qmfDeleteTime

                wait(predicate)

    class BindTopic(Test):
        def __init__(self, harness, parent):
            super(BindQueueTest.BindTopic, self).__init__(harness, parent)

            self.RemoveBindTopic(harness, self)

        def do_run(self, session):
            p, s = self.harness.page_and_session()

            p.main.broker.set_object(s, self.harness.broker.registration)
            p.main.broker.queue.set_object(s, self.harness.queue)

            form = p.main.broker.queue.binding_add
            form.show(s)

            binding = dict()
            binding["test"] = {}
            direct = binding["test"]
            direct["name"] = "amq.topic"
            direct["type"] = "topic"
            direct["key"] = "topic.key"
            form.bindings.dict_param.set(s, binding)

            form.submit(s)
            p.process(s)

            self.harness.check_redirect(p, s)

            def predicate():
                for item in Binding.selectBy(queue=self.harness.queue, bindingKey="topic.key"):
                    self.harness.binding_topic = item
                    return True

            wait(predicate)

        class RemoveBindTopic(Test):
            def do_run(self, session):
                p, s = self.harness.page_and_session()

                p.main.broker.set_object(s, self.harness.broker)

                form = p.main.broker.bindings_remove.show(s)
                form.ids.set([self.harness.binding_topic.id])
                form.submit(s)

                p.process(s)

                self.harness.check_redirect(p, s)

                def predicate():
                    return self.harness.binding_topic.qmfDeleteTime

                wait(predicate)

    class BindFanout(Test):
        def __init__(self, harness, parent):
            super(BindQueueTest.BindFanout, self).__init__(harness, parent)

            self.RemoveBindFanout(harness, self)

        def do_run(self, session):
            p, s = self.harness.page_and_session()

            p.main.broker.set_object(s, self.harness.broker.registration)
            p.main.broker.queue.set_object(s, self.harness.queue)

            form = p.main.broker.queue.binding_add
            form.show(s)

            binding = dict()
            binding["test"] = {}
            direct = binding["test"]
            direct["name"] = "amq.fanout"
            direct["type"] = "fanout"
            form.bindings.dict_param.set(s, binding)

            form.submit(s)
            p.process(s)

            self.harness.check_redirect(p, s)

            def predicate():
                for item in Binding.selectBy(queue=self.harness.queue):
                    if item.exchange.name == "amq.fanout":
                        self.harness.binding_fanout = item
                        return True

            wait(predicate)

        class RemoveBindFanout(Test):
            def do_run(self, session):
                p, s = self.harness.page_and_session()

                p.main.broker.set_object(s, self.harness.broker)

                form = p.main.broker.bindings_remove.show(s)
                form.ids.set([self.harness.binding_fanout.id])
                form.submit(s)

                p.process(s)

                self.harness.check_redirect(p, s)

                def predicate():
                    return self.harness.binding_fanout.qmfDeleteTime

                wait(predicate)

    class BindHeaders(Test):
        def do_run(self, session):
            p, s = self.harness.page_and_session()

            p.main.broker.set_object(s, self.harness.broker.registration)
            p.main.broker.queue.set_object(s, self.harness.queue)

            form = p.main.broker.queue.binding_add
            form.show(s)

            binding = dict()
            binding["test"] = {}
            direct = binding["test"]
            direct["name"] = "amq.match"
            direct["type"] = "headers"
            direct["key"] = "headers.key"
            direct["x-match"] = "all"
            direct["mkey.1"] = "key1"
            direct["mkey.1.nv"] = "name.value.1"
            form.bindings.dict_param.set(s, binding)

            form.submit(s)
            p.process(s)

            self.harness.check_redirect(p, s)

            def predicate():
                for item in Binding.selectBy(queue=self.harness.queue, bindingKey="headers.key"):
                    return True

            wait(predicate)

            # if it timed out, raise an exception
            try:
                Binding.selectBy(queue=self.harness.queue, bindingKey="headers.key")[0]
            except IndexError:
                raise Exception("Headers Binding not added")

class AddQueueTest(Test):
    def __init__(self, harness, parent):
        super(AddQueueTest, self).__init__(harness, parent)

        BindQueueTest(harness, self)

    def do_run(self, session):
        name = "cumin.queue.%s" % session.id
        p, s = self.harness.page_and_session()

        p.main.broker.set_object(s, self.harness.broker)

        form = p.main.broker.queue_add
        form.show(s)
        form.namef.set(s, name)
        form.submit(s)

        p.process(s)

        self.harness.check_redirect(p, s)

        vhost = self.harness.vhost

        # wait for newly created queue to show up
        def predicate():
            for item in Queue.selectBy(vhost=vhost, name=name):
                return True

        wait(predicate)

        # if it timed out, raise an exception
        try:
            self.harness.queue = Queue.selectBy(vhost=vhost, name=name)[0]
        except IndexError:
            raise Exception("Queue %s not added" % name)

        self.run_children(session)


class QueueTest(Test):
    def __init__(self, harness, parent):
        super(QueueTest, self).__init__(harness, parent)

        AddQueueTest(harness, self)
        self.Remove(harness, self)

    def do_run(self, session):
        vhost = self.harness.vhost
        name = self.harness.broker_queue.name

        def predicate():
            for item in Queue.selectBy(vhost=vhost, name=name):
                self.harness.broker_queue = item
                return True

        wait(predicate)

        self.run_children(session)

    class Remove(Test):
        def do_run(self, session):
            p, s = self.harness.page_and_session()

            p.main.broker.set_object(s, self.harness.broker)

            form = p.main.broker.queues_remove
            form.show(s)
            form.ids.set(s, [self.harness.queue.id])
            form.submit(s)

            p.process(s)

            self.harness.check_redirect(p, s)

            # wait for newly created queue to get marked as deleted
            def predicate():
                return self.harness.queue.qmfDeleteTime

            wait(predicate)

class AddExchangeTest(Test):
    def do_run(self, session):
        name = "cumin.exchange.%s" % session.id
        p, s = self.harness.page_and_session()

        p.main.broker.set_object(s, self.harness.broker)

        form = p.main.broker.exchange_add
        form.show(s)

        form.exchange_name.set(s, name)
        form.exchange_type.set(s, "topic")
        form.submit(s)

        p.process(s)

        self.harness.check_redirect(p, s)

        vhost = self.harness.vhost
        # wait for newly created exchange to show up
        def predicate():
            for item in Exchange.selectBy(vhost=vhost, name=name):
                self.harness.added_exchange = item
                return True

        wait(predicate)

class ExchangeTest(Test):
    def __init__(self, harness, parent):
        super(ExchangeTest, self).__init__(harness, parent)

        AddExchangeTest(harness, self)
        self.Remove(harness, self)

    def do_run(self, session):
        vhost = self.harness.vhost
        name = self.harness.broker_exchange.name

        def predicate():
            for item in Exchange.selectBy(vhost=vhost, name=name):
                self.harness.broker_exchange = item
                return True

        wait(predicate)

        self.run_children(session)

    class Remove(Test):
        def do_run(self, session):
            # try to delete it
            p, s = self.harness.page_and_session()

            p.main.broker.set_object(s, self.harness.broker)

            form = p.main.broker.exchanges_remove
            form.show(s)
            form.ids.set(s, [self.harness.added_exchange.id])
            form.submit(s)

            p.process(s)

            self.harness.check_redirect(p, s)

            # wait for newly created exchange to get marked as deleted
            def predicate():
                return self.harness.added_exchange.qmfDeleteTime

            wait(predicate)

class ConnectionTest(Test):
    def do_run(self, session):
        raise Exception("Not implemented")

        vhost = self.harness.vhost
        address = self.harness.broker_conn.host + ":" + \
            str(self.harness.broker_conn.port)

        try:
            self.harness.conn = ClientConnection.selectBy \
                (vhost=vhost, address=address)[0]
        except IndexError:
            raise Exception("ClientConnection not found")

        self.run_children(session)

def wait(predicate, timeout=30):
    start = time()

    while True:
        if predicate():
            return

        if time() - start > timeout:
            raise Exception("Operation timed out")

        sleep(1)
