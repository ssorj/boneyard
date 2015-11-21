from Queue import Queue as ConcurrentQueue, Empty as ConcurrentEmpty
from util import *

from qpid.messaging import *

log = logging.getLogger("ptolemy.common.messaging")

class MessagingThread(Thread):
    def __init__(self, url):
        super(MessagingThread, self).__init__()

        self.connection = Connection(url)
        self.connection.reconnect = True

        self.child_failed = Event()

        self.sender_thread = None
        self.receiver_thread = None

        self.addresses = list()

        self.setDaemon(True)

    def init(self):
        pass

    def queue(self, address):
        assert not self.receiver_thread
        assert address not in self.addresses, address

        self.addresses.append(address)

        return _Queue(self, address)

    def start(self):
        super(MessagingThread, self).start()

        while not self.sender_thread or not self.receiver_thread:
            time.sleep(0.1)

    def wait(self, timeout=None):
        assert self.receiver_thread, self.receiver_thread

        self.receiver_thread.wait(timeout)

    def run(self):
        while True:
            try:
                self.do_run()
            except:
                log.exception("Unexpected failure")

            time.sleep(10)

    def do_run(self):
        log.info("Connecting to %s", self.connection)

        self.connection.open()

        try:
            session = self.connection.session()

            receivers = dict()

            for address in self.addresses:
                receiver = session.receiver(address)
                receiver.capacity = UNLIMITED

                receivers[address] = receiver

            sender_thread = SenderThread(self, session)
            receiver_thread = ReceiverThread(self, session, receivers)

            sender_thread.start()
            receiver_thread.start()

            self.sender_thread = sender_thread
            self.receiver_thread = receiver_thread

            try:
                self.child_failed.wait()
            finally:
                self.sender_thread = None
                self.receiver_thread = None

                sender_thread.stop()
                receiver_thread.stop()

                self.child_failed.clear()
        finally:
            self.connection.close()

    def send(self, address, message):
        assert self.sender_thread, self.sender_thread

        self.sender_thread.put(address, message)

class _Queue(object):
    def __init__(self, thread, address):
        self.thread = thread
        self.address = address

    def get(self):
        assert self.thread.receiver_thread, self.thread.receiver_thread

        return self.thread.receiver_thread.get(self.address)

    def put(self, message):
        assert self.thread.sender_thread, self.thread.sender_thread

        self.thread.sender_thread.put(self.address, message)

class ChildThread(Thread):
    def __init__(self, parent, session):
        super(ChildThread, self).__init__()

        self.parent = parent
        self.session = session

        self.stopped = Event()

        self.setDaemon(True)

    def stop(self):
        self.stopped.set()
        self.join()

    def run(self):
        assert self.session, self.session

        try:
            self.do_run()
        except:
            log.exception("Child thread failed")

            self.parent.child_failed.set()

class SenderThread(ChildThread):
    def __init__(self, parent, session):
        super(SenderThread, self).__init__(parent, session)

        self.queue = ConcurrentQueue()

    def put(self, address, message):
        self.queue.put((address, message))

    def do_run(self):
        senders_by_address = dict()

        while True:
            if self.stopped.isSet():
                return

            #log.debug("Sender tick")

            try:
                address, message = self.queue.get(timeout=1)
            except ConcurrentEmpty:
                continue

            try:
                sender = senders_by_address[address]
            except KeyError:
                sender = self.session.sender(address)
                senders_by_address[address] = sender

            sender.send(message)

            log.debug("Sent a message")
            #pprint(message.content)

class ReceiverThread(ChildThread):
    def __init__(self, parent, session, receivers_by_address):
        super(ReceiverThread, self).__init__(parent, session)

        self.receivers_by_address = receivers_by_address
        self.queues_by_address = defaultdict(deque)

        self.lock = Condition()

    def wait(self, timeout=None):
        self.lock.acquire()

        try:
            self.lock.wait(timeout)
        finally:
            self.lock.release()

    def get(self, address):
        queue = self.queues_by_address[address]

        self.lock.acquire()

        try:
            try:
                return queue.pop()
            except IndexError:
                pass
        finally:
            self.lock.release()

    def do_run(self):
        while True:
            if self.stopped.isSet():
                return

            #log.debug("Receiver tick")

            try:
                receiver = self.session.next_receiver(timeout=1)
            except Empty:
                continue

            queue = self.queues_by_address[receiver.source]
            message = receiver.fetch()

            log.debug("Received a message")

            self.lock.acquire()

            try:
                queue.appendleft(message)

                self.lock.notify()
            finally:
                self.lock.release()
            
            self.session.acknowledge()
