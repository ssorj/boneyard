from ptolemy.common.config import *
from ptolemy.common.process import *
from ptolemy.common.server import *

log = logging.getLogger("ptolemy.masterserver")

class MasterServer(PtolemyServer):
    def __init__(self, config):
        super(MasterServer, self).__init__(config)

        self.children = list()

    def init(self):
        log.debug("Intializing %s", self)

        if self.config.alert_server_enabled:
            self.children.append(ChildServer(self, "ptolemy-alert-server"))

        if self.config.console_server_enabled:
            self.children.append(ChildServer(self, "ptolemy-console-server"))

        if self.config.file_server_enabled:
            self.children.append(ChildServer(self, "ptolemy-file-server"))

        if self.config.harness_server_enabled:
            self.children.append(ChildServer(self, "ptolemy-harness-server"))

        if self.config.model_server_enabled:
            self.children.append(ChildServer(self, "ptolemy-model-server"))

    def run(self):
        try:
            for child in self.children:
                child.start()
        except:
            for child in self.children:
                child.stop()

                raise

        try:
            while True:
                for child in self.children:
                    if not child.running():
                        log.warn("%s has stopped unexpectedly", child)

                        child.start()

                time.sleep(10)

                log.debug("Tick")
        finally:
            for child in self.children:
                child.stop()

class MasterServerConfig(ServerConfig):
    def __init__(self, home):
        super(MasterServerConfig, self).__init__(home, "master-server")

        self.data.alert_server_enabled = False
        self.data.console_server_enabled = False
        self.data.file_server_enabled = True
        self.data.harness_server_enabled = True
        self.data.model_server_enabled = False

class ChildServer(object):
    def __init__(self, master, name):
        self.master = master
        self.name = name
        self.proc = None

    def start(self):
        log.info("Starting %s", self)

        path = os.path.join(self.master.home, "bin", self.name)

        self.proc = UnixProcess(path)
        self.proc.output = open(os.devnull, "w")
        self.proc.start()

    def running(self):
        if self.proc:
            return self.proc.running()

    def stop(self):
        log.info("Stopping %s", self)

        if self.proc:
            self.proc.stop()

    def __repr__(self):
        args = self.__class__.__name__, self.name
        return "%s(%s)" % args
