import logging

from Queue import Queue as ConcurrentQueue, Empty

from summary import *
from util import *

log = logging.getLogger("ptolemy.notify")

class NotifyThread(QpidSessionThread):
    def __init__(self, server):
        super(NotifyThread, self).__init__(server.broker_addr)

        self.server = server
        self.cycles = ConcurrentQueue()

    def enqueue(self, cycle):
        self.cycles.put(cycle)

    def do_run(self, session):
        while True:
            try:
                cycle = self.cycles.get(timeout=1)
            except Empty:
                continue

            summary = CycleSummary(cycle)

            message = PtolemyMessage()
            message.destination = "amq.topic"
            message.routing_key = "ptolemy.notify"

            color = ""
            url = cycle.url

            if cycle.status == cycle.OK:
                color = "\x0303"
            elif cycle.status == cycle.FAILED:
                color = "\x0304"
                url = "%s/%s.out.gz" % (url, cycle.script_name)
            elif cycle.status == cycle.RUNNING:
                color = "\x0308"
                url = "%s/timeout.out.gz" % url

            text = summary.get_title()

            message.body = "%s\x02%s\x0f [%s]" % (color, text, url)

            message.send(session)

            log.info("Sent notification that %s", summary.get_title())
