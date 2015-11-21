from Queue import Queue as ConcurrentQueue, \
    Empty as ConcurrentEmpty, \
    Full as ConcurrentFull

from config import *
from util import *

log = logging.getLogger("ptolemy.common.server")

class PtolemyServer(object):
    def __init__(self, config):
        assert isinstance(config, ServerConfig)

        self.config = config
        self.home = config.home
        self.debug = False

        if "PTOLEMY_DEBUG" in os.environ:
            self.debug = True

    def init(self):
        log.info("Intializing %s", self)
        log.debug("Loaded configuration:\n%s", pformat(self.config.data))

    def __repr__(self):
        args = self.__class__.__name__, self.home
        return "%s(%s)" % args

class ServerConfig(PtolemyConfig):
    def __init__(self, home, component):
        super(ServerConfig, self).__init__(home, component)

        self.data.operator = None

        path = os.path.join(self.home, "log", "%s.log" % self.component)
        self.data.log_file = path

class ServerThread(Thread):
    def __init__(self, server, name):
        super(ServerThread, self).__init__()

        self.server = server
        self.name = name

        self.setDaemon(True)

    def init(self):
        pass

    def run(self):
        try:
            self.do_run()
        except KeyboardInterrupt:
            raise
        except:
            log.exception("Unexpected error")

    def __repr__(self):
        args = self.__class__.__name__, self.server, self.name
        return "%s(%s,%s)" % args
