import logging
import os

from Queue import Queue, Empty
from datetime import datetime, timedelta, time
from fnmatch import fnmatchcase
from threading import Timer
from time import sleep

from command import *
from config import *
from mail import *
from model import *
from notify import *
from util import *
from web import *

log = logging.getLogger("ptolemy.server")

class Server(object):
    def __init__(self, config):
        self.path = config.home
        self.debug = config.debug
        self.name = config.name.get()
        self.broker_addr = config.broker.get()
        self.web_addr = config.web.get()
        self.operator = config.operator.get()

        self.mail_enabled = config.mail_enable.get()
        self.mail_addrs_by_user = config.mail_addrs_by_user
        self.mail_addrs_by_project = config.mail_addrs_by_project

        self.url = "http://%s:%i" % self.web_addr

        self.projects_path = os.path.join(self.path, "projects")
        self.projects = list()
        self.projects_by_name = dict()

        self.installs_path = os.path.join(self.path, "installs")
        self.cycles_path = os.path.join(self.path, "cycles")

        self.command_thread = CommandThread(self)
        self.cycle_thread = CycleThread(self)
        self.mail_thread = MailThread(self)
        self.notify_thread = NotifyThread(self)
        self.timer_thread = TimerThread(self)
        self.web_thread = WebThread(self)

        self.handlers_by_command = dict()

        ServerInfoHandler(self)
        ProjectInfoHandler(self, "project-info")
        ProjectQueueHandler(self, "project-queue")
        CycleInfoHandler(self)

    def init(self):
        log.debug("Initializing %s", self)

        if self.debug:
            log.info("Debug is enabled")

        self.web_thread.init()

        if not os.path.exists(self.projects_path):
            os.makedirs(self.projects_path)

        if not os.path.exists(self.installs_path):
            os.makedirs(self.installs_path)

        if not os.path.exists(self.cycles_path):
            os.makedirs(self.cycles_path)

        # XXX So far this doesn't help
        # self.preload_fs_cache()

        for name in sorted(os.listdir(self.projects_path)):
            if not name.startswith(".") and name != "common":
                config = ProjectConfig(self, name)

                try:
                    config.load()
                except:
                    log.error("Failed loading configuration for project '%s'",
                              name)
                    continue

                project = Project(self, name, config)

                self.projects.append(project)
                self.projects_by_name[name] = project

        for project in self.projects:
            project.init()

        for pattern, addrs in self.mail_addrs_by_project.iteritems():
            for project in self.projects:
                if fnmatchcase(project.name, pattern):
                    project.mail_addrs.update(addrs)

        log.info("Initialized %s with %i projects", self, len(self.projects))

    def preload_fs_cache(self):
        log.debug("Preloading filesystem cache")

        for root, dirs, files in os.walk(self.cycles_path):
            for name in files:
                if name in ("props", "revision", "changes"):
                    try:
                        file = open(os.path.join(root, name), "r")
                        try:
                            file.read()
                        finally:
                            file.close()
                    except IOError, e:
                        log.exception(e)

    def start(self):
        self.command_thread.start()
        self.cycle_thread.start()
        self.mail_thread.start()
        self.notify_thread.start()
        self.timer_thread.start()
        self.web_thread.start()

    def run(self):
        self.start()

        while True:
            sleep(60)

    def __str__(self):
        return "%s(%s,%s)" % (self.__class__.__name__, self.name, self.path)

class CycleThread(ServerThread):
    def __init__(self, server):
        super(CycleThread, self).__init__(server, "cycle")

        self.requests = Queue()
        self.busy = False

    def enqueue(self, projects, force=False, deps=True):
        for project in projects:
            project.enqueue_time = unixtime_now()

        request = CycleRequest(projects, force, deps)

        log.info("Enqueueing %s", request)

        self.requests.put(request)

    def run(self):
        while True:
            try:
                request = self.requests.get(timeout=1)

                assert not self.busy
                self.busy = True

                try:
                    request.process()
                finally:
                    assert self.busy
                    self.busy = False
            except Empty:
                pass
            except KeyboardInterrupt:
                raise
            except Exception, e:
                log.exception(e)

class TimerThread(ServerThread):
    def __init__(self, server):
        super(TimerThread, self).__init__(server, "timer")

    def run(self):
        cycler = self.server.cycle_thread

        while True:
            now = datetime.now()
            secs = 3600 - ((now.minute * 60) + now.second)
            then = now + timedelta(seconds=secs)

            log.info("Sleeping until %s", then.strftime("%H:%M"))

            sleep(secs + 1)

            if not cycler.busy and cycler.requests.empty():
                cycler.enqueue(self.server.projects, force=False, deps=True)
            else:
                log.info("Cycles in progress; skipping periodic work")
