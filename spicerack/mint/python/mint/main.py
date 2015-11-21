from database import MintDatabase
from expire import ExpireThread
from model import MintModel
from session import MintSession
from update import UpdateThread
from vacuum import VacuumThread
from cumin.admin import *
from util import *

log = logging.getLogger("mint.main")

class Mint(object):
    def __init__(self, model_dir, broker_uris, database_dsn):
        self.model = MintModel(self, model_dir)
        self.model.sql_logging_enabled = False

        self.session = MintSession(self, broker_uris)
        self.database = MintDatabase(self, database_dsn)
        self.admin = CuminAdmin(self)
        self.update_thread = UpdateThread(self)

        self.expire_enabled = True
        self.expire_thread = ExpireThread(self)

        self.vacuum_enabled = True
        self.vacuum_thread = VacuumThread(self)

        self.print_event_level = 0

        # Space separated list of sasl authentication
        # mechanisms, according to the sasl documentation
        self.sasl_mech_list = None

        # List of agents to bind.  Referenced by session.
        self.qmf_agents = set()

        # List of classes to bind. Referenced by session and update thread.
        self.qmf_classes = set()

        # If binding was not done by class, this is the final list of
        # packages that were bound
        self.qmf_packages = set()

        # Things we know should not be bound.
        self.qmf_package_filter = ["com.redhat.cumin", "com.redhat.cumin.grid"]

    def check(self):
        log.info("Checking %s", self)

        self.model.check()
        self.session.check()
        self.database.check()

    def init(self):
        log.info("Initializing %s", self)

        def state(cond):
            return cond and "enabled" or "disabled"

        log.info("Expiration is %s", state(self.expire_enabled))
        log.info("Vacuum is %s", state(self.vacuum_enabled))

        self.model.init()
        self.session.init()
        self.database.init()

        self.update_thread.init()
        self.expire_thread.init()
        self.vacuum_thread.init()

    def start(self):
        log.info("Starting %s", self)

        # Scan the qmf class/package binding list
        # and do any necessary preprocessing
        self.session.init_qmf_classes()
        
        self.update_thread.start()

        self.session.start()

        if self.expire_enabled:
            self.expire_thread.start()

        if self.vacuum_enabled:
            self.vacuum_thread.start()

    def stop(self, skip_vacuum=False):
        log.info("Stopping %s", self)

        self.update_thread.stop()

        if self.expire_enabled:
            self.expire_thread.stop()
        
        if self.vacuum_enabled and not skip_vacuum:
            self.vacuum_thread.stop()

        self.session.stop()
        log.info("Session stopped")

    def __repr__(self):
        return self.__class__.__name__
