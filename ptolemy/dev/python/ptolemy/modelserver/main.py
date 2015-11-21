from ptolemy.common.config import *
from ptolemy.common.messaging import *
from ptolemy.common.model import *
from ptolemy.common.server import *

class ModelServer(PtolemyServer):
    def __init__(self, config):
        super(ModelServer, self).__init__(config)

        self.model = Model()

        self.messaging_thread = MessagingThread(self.config.broker)

        addr = ptolemy_model_update_address
        self.updates = self.messaging_thread.queue(addr)

        addr = ptolemy_model_request_address
        self.requests = self.messaging_thread.queue(addr)

    def init(self):
        super(ModelServer, self).init()

        self.messaging_thread.init()

    def start(self):
        self.messaging_thread.start()

    def run(self):
        self.start()

        while True:
            self.messaging_thread.wait(timeout=86400)

            try:
                self.process_updates()
            except:
                log.exception("Failed processing updates")

            try:
                self.service_requests()
            except:
                log.exception("Failed servicing requests")

    def process_updates(self):
        log.debug("Processing updates")

        while True:
            message = self.updates.get()
            
            if not message:
                break

            self.model.unmarshal(message.content)

    def service_requests(self):
        log.debug("Servicing requests")

        while True:
            message = self.requests.get()

            if not message:
                break

            log.debug("Sending model data")

            data = self.model.marshal()
            self.messaging_thread.send(message.reply_to, Message(data))
