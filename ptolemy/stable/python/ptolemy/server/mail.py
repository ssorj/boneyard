import sys
import os
import logging

from smtplib import *
from Queue import Queue, Empty
from threading import Thread

from summary import *
from util import *

log = logging.getLogger("ptolemy.mail")

class MailThread(ServerThread):
    def __init__(self, server):
        super(MailThread, self).__init__(server, "mail")

        self.cycles = Queue()

    def enqueue(self, cycle):
        if self.server.mail_enabled:
            self.cycles.put(cycle)

    def run(self):
        while True:
            try:
                cycle = self.cycles.get(timeout=1)
            except Empty:
                continue

            try:
                if cycle.status == cycle.RUNNING:
                    message = CycleTimedOutMessage(cycle)
                else:
                    message = CycleStatusMessage(cycle)

                message.send()
            except:
                log.exception("Unexpected error")

class MailMessage(CycleSummary):
    def __init__(self, cycle):
        super(MailMessage, self).__init__(cycle)

        self.from_addr = self.cycle.project.server.operator
        self.to_addrs = self.generate_to_addrs()

    def generate_to_addrs(self):
        # For update errors, only mail the operator
        if self.cycle.status == self.cycle.FAILED and \
                self.cycle.script_name == "update":
            return (self.cycle.project.server.operator,)

        addrs = set()

        addrs.update(self.cycle.project.owners)
        addrs.update(self.cycle.project.mail_addrs)

        def update_addrs(cycle):
            addrs_by_user = self.cycle.project.server.mail_addrs_by_user

            for change in cycle.changes:
                try:
                    addrs.update(addrs_by_user[change[1]])
                except KeyError:
                    pass

        update_addrs(self.cycle)

        for cycle in self.cycle.required_cycles():
            update_addrs(cycle)

        return sorted(addrs)

    def send(self):
        body = self.get_body()

        if self.cycle.project.server.debug:
            log.debug("Not sending mail since debug is enabled")
            log.debug("I would have sent mail to %s" % \
                          ", ".join(self.to_addrs))

            return

        smtp = SMTP()

        try:
            smtp.connect()

            try:
                smtp.sendmail(self.from_addr, self.to_addrs, body)
            finally:
                smtp.quit()
        except Exception, e:
            log.error("Failed sending mail: %s", e)

class CycleTimedOutMessage(MailMessage):
    def get_body(self):
        out = list()

        out.append("From: %s" % self.from_addr)
        out.append("To: %s" % ", ".join(self.to_addrs))
        out.append("Subject: [ptol] %s" % self.get_title())

        out.append("")

        self.generate_properties(out)

        out.append("")

        self.generate_changes(out)

        out.append("")

        self.generate_output(out, "timeout")

        return "\r\n".join(out)

class CycleStatusMessage(MailMessage):
    def get_body(self):
        out = list()

        out.append("From: %s" % self.from_addr)
        out.append("To: %s" % ", ".join(self.to_addrs))
        out.append("Subject: [ptol] %s" % self.get_title())

        out.append("")

        self.generate_properties(out)

        out.append("")

        self.generate_changes(out)

        out.append("")

        if self.cycle.status == self.cycle.FAILED:
            self.generate_output(out, self.cycle.script_name)

            out.append("")

        return "\r\n".join(out)
