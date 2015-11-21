from ptolemy.common.config import *
from ptolemy.common.model import *
from ptolemy.common.messaging import *
from ptolemy.common.server import *

from mail import *

log = logging.getLogger("ptolemy.alertserver")

class AlertServer(PtolemyServer):
    def __init__(self, config):
        super(AlertServer, self).__init__(config)

        self.model = Model()

        self.messaging_thread = MessagingThread(self.config.broker)
        self.mail_thread = MailThread(self)
        #self.chat_thread = ChatThread(self)

        addr = ptolemy_model_update_address
        self.updates = self.messaging_thread.queue(addr)

    def init(self):
        super(AlertServer, self).init()

        self.messaging_thread.init()
        self.mail_thread.init()
        #self.chat_thread.init()

    def start(self):
        self.messaging_thread.start()
        self.mail_thread.start()
        #self.chat_thread.start()

    def run(self):
        self.start()
        
        while True:
            self.messaging_thread.wait(timeout=86400)

            log.debug("Tick")

            try:
                self.update_model()
            except:
                log.exception("Failed updating model")

            try:
                self.process_updates()
            except:
                log.exception("Failed processing updates")

    def update_model(self):
        log.debug("Updating model")

        update = self.updates.get()

        if not update:
            return

        self.model.unmarshal(update.content)

    def process_updates(self):
        log.debug("Processing updates")

        now = time.time()

        fn = lambda x: x.start_time
        cycles = reversed(sorted(self.model.cycles_by_id.values(), key=fn))

        for cycle in cycles:
            if cycle.start_time < now:
                break

            if cycle.is_news():
                self.mail_thread.cycles.put(cycle)

class AlertServerConfig(ServerConfig):
    def __init__(self, home):
        super(AlertServerConfig, self).__init__(home, "alert-server")

        mail = ObjectDict()
        mail.enabled = True
        mail.default_recipients = list()

        self.data.mail = mail
