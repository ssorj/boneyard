from mint.database import MintDatabase
from mint.expire import ExpireThread
from mint.model import MintModel
from mint.vacuum import VacuumThread
from session import PlumageSession
from update import UpdateThread
from cumin.admin import CuminAdmin
#from util import *

import logging

log = logging.getLogger("mint.plumage")

class Plumage(object):
    def __init__(self, model_dir, server_host, server_port, database_dsn):

        # Can we just use a different model dir here?
        # That would control visible packages, vacuuming, etc.
        self.model = MintModel(self, model_dir)
        self.model.sql_logging_enabled = False

        self.database = MintDatabase(self, database_dsn)
        self.admin = CuminAdmin(self)
        self.update_thread = UpdateThread(self)
        self.session = PlumageSession(self, server_host, server_port)

        self.expire_enabled = True
        self.expire_thread = ExpireThread(self)

        self.vacuum_enabled = True
        self.vacuum_thread = VacuumThread(self)
        
        self.plumage_host = "localhost"
        self.plumage_port = 27017

        self.print_event_level = 0

        self.packages = set()

        self.classes = set()

        self.package_filter = ["com.redhat.cumin"]

    def check(self):
        log.info("Checking %s", self)

        self.model.check()
        self.database.check()
        self.model.init()

    def init(self):
        log.info("Initializing %s", self)

        def state(cond):
            return cond and "enabled" or "disabled"

        log.info("Expiration is %s", state(self.expire_enabled))
        log.info("Vacuum is %s", state(self.vacuum_enabled))

        self.database.init()

        self.update_thread.init()
        self.session.init()        
        # The package and class lists will be
        # processed here
        self.session.init_classes()

        if self.expire_enabled:
            self.expire_thread.init()

        if self.vacuum_enabled:
            self.vacuum_thread.init()

    def start(self):
        log.info("Starting %s", self)

        self.update_thread.start()

        self.session.start()

        if self.expire_enabled:
            # If we set these values here, we can have each cumin-report
            # instance run expiration for its own classes...
            # Default is like cumin-data, where a single instance runs
            # expiration across all classes in the model
            #self.expire_thread.packages = self.packages
            #self.expire_thread.classes = self.classes
            self.expire_thread.start()

        if self.vacuum_enabled:
            self.vacuum_thread.start()

    def stop(self):
        log.info("Stopping %s", self)

        self.update_thread.stop()
        self.session.stop()

        if self.expire_enabled:
            self.expire_thread.stop()

        if self.vacuum_enabled:
            self.vacuum_thread.stop()

    def __repr__(self):
        return self.__class__.__name__
