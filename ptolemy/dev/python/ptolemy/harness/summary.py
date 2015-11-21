import gzip

from ptolemy.common.util import *

log = logging.getLogger("ptolemy.harness.summary")

class CycleSummary(object):
    def __init__(self, cycle):
        self.cycle = cycle

    def get_title(self):
        server = self.cycle.project.model.harness.name # XXX a misnomer now
        project = self.cycle.project.name
        status = self.cycle.status_text()

        if self.cycle.status == self.cycle.RUNNING:
            script = self.cycle.running_scripts[-1].name

            text = "%s %s is taking too long on %s" % (project, script, server)
        else:
            text = "%s %s on %s" % (project, status, server)

        return text

    def get_body(self):
        out = list()

        self.generate_properties(out)

        out.append("")

        self.generate_changes(out)

        if self.cycle.status == self.cycle.FAILED:
            out.append("")

            self.generate_output(out, self.cycle.script_name)

        return os.linesep.join(out)

    def generate_properties(self, out):
        out.append("Cycle")
        out.append("")

        out.append("  %-10s  %s" % ("Status", self.cycle.status_text()))
        out.append("  %-10s  %s" % \
                       ("Server", self.cycle.project.model.harness.name))
        out.append("  %-10s  %s" % ("Project", self.cycle.project.name))
        out.append("  %-10s  %s" % ("Revision", self.cycle.revision or "-"))

        stime = fmt_local_unixtime(self.cycle.start_time)
        etime = fmt_local_unixtime(self.cycle.end_time)

        out.append("  %-10s  %s" % ("Start time", stime))
        out.append("  %-10s  %s" % ("End time", etime))

        out.append("  %-10s  %s" % ("URL", self.cycle.uri))

    def generate_changes(self, out):
        out.append("Changes")
        out.append("")

        changes = set(self.cycle.changes)

        for cycle in self.cycle.required_cycles():
            changes.update(cycle.changes)

        if changes:
            for change in sorted(changes):
                out.append("  %-10s  %s" % change)
        else:
            out.append("  [None]")

    def generate_output(self, out, script_name):
        output = "%s.out.gz" % script_name

        out.append("Output")
        out.append("")
        out.append("  [%s/%s]" % (self.cycle.uri, output))
        out.append("")

        path = os.path.join(self.cycle.path, output)
        size = os.path.getsize(path)

        if size < 10**6:
            file = gzip.open(path, "rb")

            try:
                lines = file.readlines()
            finally:
                file.close()

            if len(lines) > 128:
                lines = lines[-128:]
                out.append("  [snip]")

            for line in lines:
                out.append("  %s" % line[:-1])
