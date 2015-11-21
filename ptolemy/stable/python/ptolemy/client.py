import sys, os, logging
from qpid import *
from qpid.connection import *
from qpid.datatypes import *
from qpid.util import *
from Queue import Empty

from util import *

log = logging.getLogger("ptolemy.client")

def vt100_attrs(*attrs):
    return "\x1B[%sm" % ";".join(map(str, attrs))

vt100_reset = vt100_attrs(0)

COLORS = {"ok": (32,),
          "failed": (31,),
          "running": (34,)}

def colorize_status(text, status):
    return colorize(text, *COLORS.get(status, ()))

def colorize(text, *attrs):
    term = os.environ.get("TERM", "dumb")

    if attrs and term != "dumb":
        return "%s%s%s" % (vt100_attrs(*attrs), text, vt100_reset)
    else:
        return text

class PtolemyClient(object):
    def __init__(self):
        id = short_id()

        self.news_queue = "ptolemy.client.%s.news" % id
        self.response_queue = "ptolemy.client.%s.response" % id

        self.commands = list()
        self.commands_by_name = dict()

        ProjectStatusCommand(self, "status")
        ProjectQueueCommand(self, "queue")

        ProjectLogCommand(self)
        CycleInfoCommand(self)
        ServerInfoCommand(self)

    def init(self):
        for command in self.commands:
            command.init()

    def print_usage(self):
        print "Usage: ptol COMMAND"
        print "Commands:"

        for cmd in self.commands:
            if cmd.aliases:
                names = "%s (%s)" % (cmd.name, ", ".join(cmd.aliases))
            else:
                names = cmd.name

            print "  %-30s  %s" % (names, cmd.description)

    def setup_broker_wiring(self, session):
        session.queue_declare(queue=self.news_queue, exclusive=True,
                              auto_delete=True)
        session.exchange_bind(exchange="amq.topic", queue=self.news_queue,
                              binding_key="ptolemy.news")

        session.queue_declare(queue=self.response_queue, exclusive=True,
                              auto_delete=True)
        session.exchange_bind(exchange="amq.direct", queue=self.response_queue,
                              binding_key=self.response_queue)

class Command(object):
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.aliases = ()
        self.arguments = ()
        self.options = list()
        self.options_by_param = dict()
        self.description = None

        self.client.commands.append(self)
        self.client.commands_by_name[self.name] = self

        opt = CommandOption(self, "help", "h")
        opt.description = "Print this message"

    def init(self):
        for alias in self.aliases:
            self.client.commands_by_name[alias] = self

        for option in self.options:
            option.init()

    def parse(self, argv):
        opts = dict()
        args = list()
        opt = None

        def find_opt(key):
            try:
                opt = self.options_by_param[key]
                opts[opt.name] = None
                return opt
            except KeyError:
                msg = "Option '%s' is unrecognized" % key
                raise CommandException(self, msg)

        for arg in argv:
            if arg.startswith("--"):
                opt = find_opt(arg[2:])
            elif arg.startswith("-"):
                opt = find_opt(arg[1])
            elif opt:
                if opt.argument:
                    opts[opt.name] = opt.unmarshal(arg)
                    opt = None
                else:
                    args.append(arg)
            else:
                args.append(arg)

        return opts, args

    def print_usage(self):
        summary = "ptol %s" % self.name

        if self.options:
            summary = summary + " [OPTIONS]"

        if self.arguments:
            summary = summary + " " + " ".join(self.arguments)

        print "Usage: %s" % summary
        print "Options:"

        for opt in self.options:
            osummary = "--%s" % opt.name

            if opt.char:
                osummary = osummary + " (-%s)" % opt.char

            if opt.argument:
                osummary = osummary + " " + opt.argument

            print "  %-30s  %s" % (osummary, opt.description)

    def parse_cycle_path(self, path):
        server = None
        project = None
        cycle = None

        elems = path.split(":")

        for elem in elems:
            if elem == "":
                raise CommandException(self, "Cycle path is malformed")

        if len(elems) == 2:
            server, project = elems
        elif len(elems) == 3:
            server, project, cycle = elems
        else:
            raise CommandException(self, "Cycle path is malformed")

        return (server, project, cycle)

    def print_server(self, resp):
        print "Server '%s':" % resp.get("server")

    def process_response(self, resp):
        messages = resp.get("messages")
        errors = resp.get("errors")

        if messages:
            for m in messages:
                print "  %s" % m

        if errors:
            for e in errors:
                print "  Error: %s" % e

            return errors

class CommandOption(object):
    def __init__(self, command, name, char=None):
        self.command = command
        self.name = name
        self.char = char
        self.argument = None
        self.description = None
        self.type = str

        self.command.options.append(self)
        self.command.options_by_param[self.name] = self

    def init(self):
        if self.char:
            self.command.options_by_param[self.char] = self

    def unmarshal(self, value):
        return self.type(value)

class CommandException(Exception):
    def __init__(self, command, message):
        self.command = command
        self.message = message

class RequestMessage(PtolemyMessage):
    def __init__(self, command, response_queue):
        super(RequestMessage, self).__init__()

        self.destination = "amq.topic"
        self.routing_key = "ptolemy.request"
        self.response_queue = response_queue
        self.set("command", command)

    def start_response_queue(self, session):
        name = long_id()
        session.message_subscribe(queue=self.response_queue, destination=name)
        incoming = session.incoming(name)
        incoming.start()

        return incoming

class ProjectQueueCommand(Command):
    def __init__(self, client, name):
        super(ProjectQueueCommand, self).__init__(client, name)

        self.arguments = ("PROJECTS...",)
        self.description = "Queue new cycles for PROJECTS"

        opt = CommandOption(self, "server", "s")
        opt.argument = "SERVER"
        opt.description = "Run PROJECTS only on SERVER"

        opt = CommandOption(self, "force")
        opt.description = "Run even if PROJECT is not updated"

        opt = CommandOption(self, "no-deps")
        opt.description = "Skip running dependencies of PROJECT"

    def run(self, session, opts, args):
        if len(args) < 1:
            raise CommandException(self, "At least one PROJECT is required")

        req = RequestMessage("project-queue", self.client.response_queue)
        req.set("projects", args)
        req.set("server", opts.get("server", "*"))
        req.set("force", "force" in opts)
        req.set("deps", "no-deps" not in opts)
        req.send(session)

        incoming = req.start_response_queue(session)

        try:
            while True:
                msg = incoming.get(timeout=1)
                session.message_accept(RangedSet(msg.id))

                resp = PtolemyMessage()
                resp.unmarshal(msg)

                self.print_server(resp)
                self.process_response(resp)
        except Empty:
            pass

class ProjectStatusCommand(Command):
    def __init__(self, client, name):
        super(ProjectStatusCommand, self).__init__(client, name)

        self.aliases = ("stat", "st")
        self.arguments = ("PROJECTS...",)
        self.description = "Check status of PROJECTS"

        self.headers = ("Project", "Cycle", "Revision", "Time", "Status")
        self.cols = "  %-28s  %6s  %-8s  %6s  %s"

        opt = CommandOption(self, "server", "s")
        opt.argument = "SERVER"
        opt.description = "Only show projects matching SERVER"

        opt = CommandOption(self, "status", "t")
        opt.argument = "STATUS"
        opt.description = "Only show projects in STATUS ('failed', 'ok', 'running')"

    def print_headers(self, resp):
        print (self.cols % self.headers).rstrip()
        print "  %s" % ("-" * 78)

    def print_row(self, *args):
        print (self.cols % args).rstrip()

    def run(self, session, opts, args):
        req = RequestMessage("project-info", self.client.response_queue)
        req.set("projects", args or "*")
        req.set("server", opts.get("server", "*"))
        req.send(session)

        incoming = req.start_response_queue(session)

        only_status = opts.get("status")

        try:
            while True:
                msg = incoming.get(timeout=1)
                session.message_accept(RangedSet(msg.id))

                resp = PtolemyMessage()
                resp.unmarshal(msg)

                self.print_server(resp)

                self.process_response(resp)

                self.print_headers(resp)

                for project in resp.get("projects", ()):
                    name = project.get("name")

                    cycles = project.get("cycles")

                    if cycles:
                        cycle = cycles[0]
                    else:
                        continue

                    status = cycle.get("status")

                    if only_status and only_status != status:
                        continue

                    if status == "disabled":
                        continue

                    id = cycle.get("id")
                    rev = cycle.get("revision") or "-"
                    time = cycle.get("end_time") or cycle.get("start_time")
                    ftime = fmt_local_unixtime_brief(time)

                    text = cycle.get("status_text")
                    enqueue_time = cycle.get("enqueue_time")

                    if enqueue_time:
                        when = fmt_local_unixtime_brief(enqueue_time)
                        text = "%s [%s]" % (text, when)

                    text = colorize_status(text, status)

                    self.print_row(trunc(name, 28), id, rev, ftime, text)

                    error_url = cycle.get("error_url")

                    if error_url:
                        print colorize("   + %s" % error_url, 2)
        except Empty:
            pass

class ProjectLogCommand(Command):
    def __init__(self, client):
        super(ProjectLogCommand, self).__init__(client, "log")

        self.description = "Get cycle history of PROJECTS"

        self.arguments = ("PROJECTS...",)

        opt = CommandOption(self, "server", "s")
        opt.argument = "SERVER"
        opt.description = "Only show projects at SERVER"

        #opt = CommandOption(self, "status", "t")
        #opt.argument = "STATUS"
        #opt.description = "Only show cycles in STATUS ('failed', 'ok', 'running')"

        opt = CommandOption(self, "limit", "l")
        opt.argument = "COUNT"
        opt.type = int
        opt.description = "Limit number of results to COUNT (default 4)"

        self.headers = ("Cycle", "Revision", "Time", "Status")
        self.cols = "  %-36s  %-8s  %12s  %s"

    def print_headers(self):
        print (self.cols % self.headers).rstrip()
        print "  %s" % ("-" * 78)

    def print_row(self, *args):
        print (self.cols % args).rstrip()

    def run(self, session, opts, args):
        if len(args) < 1:
            raise CommandException(self, "At least one PROJECT is required")

        req = RequestMessage("project-info", self.client.response_queue)
        req.set("projects", args)
        req.set("server", opts.get("server", "*"))
        req.set("limit", opts.get("limit", 4))
        req.send(session)

        incoming = req.start_response_queue(session)

        try:
            while True:
                msg = incoming.get(timeout=1)
                session.message_accept(RangedSet(msg.id))

                resp = PtolemyMessage()
                resp.unmarshal(msg)

                self.print_server(resp)

                if self.process_response(resp):
                    continue

                self.print_headers()

                for project in resp.get("projects"):
                    for cycle in project["cycles"]:
                        args = (cycle.get("server"), cycle.get("project"),
                                cycle.get("cycle"))

                        id = "%s:%s:%i" % args
                        rev = cycle.get("revision") or "-"
                        time = cycle.get("end_time") or resp.get("start_time")
                        ftime = fmt_local_unixtime_medium(time)
                        text = cycle.get("status_text")

                        text = colorize_status(text, cycle.get("status"))

                        self.print_row(id, rev, ftime, text)

                        error_url = cycle.get("error_url")

                        if error_url:
                            print colorize(" + %s" % error_url, 2)
        except Empty:
            pass

class ServerInfoCommand(Command):
    def __init__(self, client):
        super(ServerInfoCommand, self).__init__(client, "server-info")

        self.aliases = ("si",)
        self.description = "Get info about servers"

    def run(self, session, opts, args):
        req = RequestMessage(self.name, self.client.response_queue)
        req.send(session)

        incoming = req.start_response_queue(session)

        try:
            while True:
                msg = incoming.get(timeout=1)
                session.message_accept(RangedSet(msg.id))

                resp = PtolemyMessage()
                resp.unmarshal(msg)

                if self.process_response(resp):
                    continue

                self.print_server(resp)

                print "  %s" % resp.get("uname_nodename")

                os = resp.get("redhat_release")
                arch = resp.get("uname_machine")

                print "  %s %s" % (os, arch)

                kern = resp.get("uname_sysname")
                rel = resp.get("uname_release")
                ver = resp.get("uname_version")

                print "  %s %s %s" % (kern, rel, ver)

                avgs = resp.get("load_averages").split(",")

                print "  Load averages: %s" % ", ".join(avgs)
        except Empty:
            pass

class CycleInfoCommand(Command):
    def __init__(self, client):
        super(CycleInfoCommand, self).__init__(client, "info")

        self.arguments = ("SERVER:PROJECT:CYCLE",)
        self.description = "Get info about cycle CYCLE"

    def run(self, session, opts, args):
        if len(args) < 1:
            raise CommandException(self, "Cycle path is missing")

        server, project, cycle = self.parse_cycle_path(args[0])

        req = RequestMessage("cycle-info", self.client.response_queue)
        req.set("server", server)
        req.set("project", project)
        req.set("cycle", cycle)
        req.send(session)

        incoming = req.start_response_queue(session)

        try:
            while True:
                msg = incoming.get(timeout=1)
                session.message_accept(RangedSet(msg.id))

                resp = PtolemyMessage()
                resp.unmarshal(msg)

                self.print_server(resp)

                if self.process_response(resp):
                    continue

                args = (resp.get("server"), resp.get("project"),
                        resp.get("id"))

                print "  %-10s  %s" % ("Project", resp.get("project"))
                print "  %-10s  %s" % ("Cycle", resp.get("id"))
                print "  %-10s  %s" % ("Status", resp.get("status_text"))
                print "  %-10s  %s" % ("Revision", resp.get("revision") or "-")

                stime = resp.get("start_time")
                stime = fmt_local_unixtime(stime)

                etime = resp.get("end_time")

                if etime:
                    etime = fmt_local_unixtime(etime)
                else:
                    etime = "-"

                print "  %-10s  %s" % ("Start time", stime)
                print "  %-10s  %s" % ("End time", etime)

                print "  %-10s  %s" % ("URL", resp.get("url"))
        except Empty:
            pass

def trunc(string, limit):
    if len(string) >= limit:
        return string[:limit]
    else:
        return string
