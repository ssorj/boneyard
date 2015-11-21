from ptolemy.common.config import *
from ptolemy.common.server import *

from http import *

log = logging.getLogger("ptolemy.fileserver")

class FileServer(PtolemyServer):
    def __init__(self, config):
        super(FileServer, self).__init__(config)

        self.cycles_path = os.path.join(self.home, "cycles")

        self.http_thread = HttpThread(self)

    def init(self):
        super(FileServer, self).init()

        self.http_thread.init()

    def start(self):
        log.debug("Starting %s", self)

        self.http_thread.start()

    def run(self):
        self.start()

        while True:
            time.sleep(86400)

class FileServerConfig(ServerConfig):
    def __init__(self, home):
        super(FileServerConfig, self).__init__(home, "file-server")

        self.data.http_host = "0.0.0.0"
        self.data.http_port = 10101
