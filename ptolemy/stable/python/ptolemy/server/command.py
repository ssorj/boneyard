import logging
import os

from qpid import *
from qpid.connection import *
from qpid.datatypes import *
from qpid.exceptions import *
from qpid.util import *
from time import sleep
from fnmatch import fnmatch

from util import *

log = logging.getLogger("ptolemy.server.command")

class CommandThread(QpidSessionThread):
    def __init__(self, server):
        super(CommandThread, self).__init__(server.broker_addr)

        self.log = log
        self.server = server
        self.queue = "ptolemy.server.%s.request" % short_id()

    def do_run(self, session):
        session.queue_declare(queue=self.queue, exclusive=True,
                              auto_delete=True)
        session.exchange_bind(exchange="amq.topic", queue=self.queue,
                              binding_key="ptolemy.request")
        session.message_subscribe(queue=self.queue, destination="incoming")

        incoming = session.incoming("incoming")
        incoming.start()

        while True:
            msg = incoming.get(10)
            session.message_accept(RangedSet(msg.id))

            req = PtolemyMessage()
            req.unmarshal(msg)

            command = req.get("command")

            log.info("Command: %s %s %s", command,
                     req.response_queue, str(req.headers))

            try:
                handler = self.server.handlers_by_command[command]
            except KeyError:
                log.warning("Command '%s' is unknown" % command)
                continue

            try:
                handler.run(session, req)
            except Exception, e:
                log.exception("Command handler failed")

class ResponseMessage(PtolemyMessage):
    def __init__(self, handler, req):
        super(ResponseMessage, self).__init__()

        self.destination = "amq.direct"
        self.routing_key = req.response_queue
        self.set("server", handler.server.name)

        self.errors = list()
        self.set("errors", self.errors)

        self.messages = list()
        self.set("messages", self.messages)

    def add_error(self, error):
        self.errors.append(error)

    def add_message(self, message):
        self.messages.append(message)

class CommandHandler(object):
    def __init__(self, server, command):
        self.server = server
        self.command = command

        log.info("Registering handler for command '%s'" % self.command)

        self.server.handlers_by_command[self.command] = self

    def run(self, session, req):
        resp = ResponseMessage(self, req)

        try:
            self.do_run(req, resp)

            resp.send(session)
        except ResponseCancelled:
            log.debug("Response cancelled")

    def do_run(self, req, resp):
        raise Exception("Not implemented")

class ResponseCancelled(Exception):
    pass

class ProjectCommandHandler(CommandHandler):
    def do_run(self, req, resp):
        server = req.get("server")

        assert server

        if not fnmatch(self.server.name, server):
            log.debug("Command is not directed at this server")
            raise ResponseCancelled()

        projects = list()
        patterns = req.get("projects")

        for pattern in patterns:
            matched = False

            for project in self.server.projects:
                if fnmatch(project.name, pattern):
                    matched = True
                    projects.append(project)

            if not matched:
                resp.add_error("No matches found for project '%s'" % pattern)

        try:
            self.run_projects(req, resp, projects)
        except Exception, e:
            text = "Command unexpectedly failed: %s" % str(e)
            resp.add_error(text)
            log.exception(text)

class ProjectInfoHandler(ProjectCommandHandler):
    def run_projects(self, req, resp, projects):
        limit = req.get("limit", 1)
        out = list()

        for project in projects:
            attrs = dict()
            attrs["name"] = project.name
            attrs["enqueue_time"] = project.enqueue_time

            cycles = list()

            i = 0

            for cycle in reversed(project.cycles):
                if cycle.status in (cycle.RUNNING, cycle.FAILED, cycle.OK):
                    cycles.append(cycle.message().headers)

                    i += 1

                    if i == limit:
                        break

            attrs["cycles"] = cycles

            out.append(attrs)

        resp.set("projects", out)

# XXX Call this CycleRequestHandler instead

class ProjectQueueHandler(ProjectCommandHandler):
    def run_projects(self, req, resp, projects):
        force = req.get("force") == True
        deps = req.get("deps") == True

        self.server.cycle_thread.enqueue(projects, force=force, deps=deps)

        for project in projects:
            resp.add_message("Project '%s' is queued" % project.name)

class CycleInfoHandler(CommandHandler):
    def __init__(self, server):
        super(CycleInfoHandler, self).__init__(server, "cycle-info")

    def do_run(self, req, resp):
        server = req.get("server")

        assert server

        if not fnmatch(self.server.name, server):
            log.debug("Command is not directed at this server")
            return

        try:
            sproject = req.get("project")
            project = self.server.projects_by_name[sproject]
        except KeyError:
            resp.add_error("Project '%s' is unknown" % sproject)
            pass

        try:
            sid = req.get("cycle")
            id = int(sid)
        except TypeError:
            resp.add_error("Cycle ID '%s' is malformed" % sid)
            return

        try:
            cycle = project.cycles_by_id[id]
        except KeyError:
            resp.add_error("Cycle %i is unknown" % id)
            return

        resp.set("server", self.server.name)
        resp.set("project", project.name)
        cycle.set_message_headers(resp.headers)

class ServerInfoHandler(CommandHandler):
    def __init__(self, server):
        super(ServerInfoHandler, self).__init__(server, "server-info")

    def do_run(self, req, resp):
        names = ("uname_sysname", "uname_nodename", "uname_release",
                 "uname_version", "uname_machine")

        for name, value in zip(names, os.uname()):
            resp.set(name, value)

        averages = "%.2f,%.2f,%.2f" % os.getloadavg()
        resp.set("load_averages", averages)

        try:
            release = load("/etc/redhat-release")
            resp.set("redhat_release", release.strip())
        except IOError:
            pass
