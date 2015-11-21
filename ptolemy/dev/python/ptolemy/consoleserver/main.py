from ptolemy.common.config import *
from ptolemy.common.messaging import *
from ptolemy.common.model import *
from ptolemy.common.server import *

from web import *

log = logging.getLogger("ptolemy.consoleserver")

class ConsoleServer(PtolemyServer):
    def __init__(self, config):
        super(ConsoleServer, self).__init__(config)

        self.model = Model()

        self.messaging_thread = MessagingThread(self.config.broker)
        self.web_thread = WebThread(self)

        addr = ptolemy_model_update_address
        self.updates = self.messaging_thread.queue(addr)

    def init(self):
        super(ConsoleServer, self).init()

        self.messaging_thread.init()
        self.web_thread.init()

    def start(self):
        self.messaging_thread.start()
        self.web_thread.start()

    def run(self):
        self.start()

        conn = Connection(self.config.broker)
        conn.open()

        try:
            session = conn.session()
            self.model.fetch_update(session)
        finally:
            conn.close()

        while True:
            self.messaging_thread.wait(timeout=86400)

            try:
                self.process_updates()
            except:
                log.exception("Failed processing updates")

    def process_updates(self):
        log.debug("Processing updates")

        while True:
            message = self.updates.get()
            
            if not message:
                break

            self.model.unmarshal(message.content)

class ConsoleServerConfig(ServerConfig):
    def __init__(self, home):
        super(ConsoleServerConfig, self).__init__(home, "console-server")

        self.data.host = "0.0.0.0"
        self.data.port = 11111
