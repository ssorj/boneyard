from smtplib import SMTP

from ptolemy.common.server import *

log = logging.getLogger("ptolemy.alertserver.smtp")

class MailThread(ServerThread):
    def __init__(self, server):
        super(MailThread, self).__init__(server, "mail")

        self.cycles = ConcurrentQueue()

        self.status_message = StatusMessage()
        
    def init(self):
        log.debug("Initializing %s", self)

    def do_run(self):
        while True:
            try:
                cycle = self.cycles.get(timeout=1)
            except ConcurrentEmpty:
                continue

            if not self.server.config.mail.enabled:
                log.debug("Mail is disabled")
                continue

            from_addr = self.server.config.operator
            to_addrs = self.server.config.mail.default_recipients 
            content = self.status_message.render(cycle)

            if self.server.debug:
                log.debug("Mail message:\n%s", content)
                continue

            smtp = SMTP()
            smtp.connect()

            try:
                smtp.sendmail(from_addr, to_addrs, content)
            finally:
                smtp.quit()

class StatusMessage(object):
    def render(self, cycle):
        lines = list()

        self.render_header(cycle, lines)
        self.render_properties(cycle, lines)
        self.render_test_results(cycle, lines)
        self.render_changes(cycle, lines)
        self.render_outputs(cycle, lines)

        return "\r\n".join(lines)

    def render_header(self, cycle, lines):
        lines.append("From: justin.ross@gmail.com")
        lines.append("To: justin.ross@gmail.com")

        args = (
            cycle.branch.id,
            cycle.status_message,
            "%s %s %s" % cycle.harness.env_key,
            )
                    
        lines.append("Subject: [ptol] %s: %s [%s]" % args)
        lines.append("")

    def render_properties(self, cycle, lines):
        harness = cycle.harness
        env = "%s %s %s" % harness.env_key

        props = (
            ("Status", cycle.status_message),
            ("Environment", env),
            ("Project", cycle.branch.project.name),
            ("Branch", cycle.branch.name),
            ("Revision", cycle.revision),
            ("Start time", fmt_local_unixtime(cycle.start_time)),
            ("End time", fmt_local_unixtime(cycle.end_time)),
            ("Host", harness.domain_name),
            ("ID", cycle.id),
            ("URL", cycle.url),
            )

        lines.append("Cycle")
        lines.append("")

        for name, value in props:
            self.render_property(name, value, lines)

        lines.append("")

    def render_property(self, name, value, lines):
        if value is None:
            value = "[none]"

        args = name, value
        lines.append("  %-12s  %s" % args)

    def render_test_results(self, cycle, lines):
        lines.append("Test results")
        lines.append("")

        for result in cycle.test_results:
            self.render_test_result(result, lines)

        lines.append("")

    def render_test_result(self, result, lines):
        args = result.cycle.url, result.output_file
        url = "%s/%s" % args

        args = result.test.name, url

        if result.exit_code == 0:
            lines.append("  %s passed: %s" % args)
        else:
            lines.append("  %s failed: %s" % args)

    def render_changes(self, cycle, lines):
        lines.append("Changes")
        lines.append("")

        if cycle.changes:
            changes = cycle.changes.strip()

            for line in changes.split("\n"):
                lines.append("  %s" % line)
        else:
            lines.append("  [none]")

        lines.append("")

    def render_outputs(self, cycle, lines):
        for result in cycle.test_results:
            if result.exit_code != 0:
                self.render_output(result, lines)

    def render_output(self, result, lines):
        lines.append("Output of test '%s'" % result.test.name)
        lines.append("")

        if result.output_sample:
            sample = result.output_sample.strip()

            for line in sample.split("\n"):
                lines.append("  %s" % line)
        else:
            lines.append("  [none]")

        lines.append("")
