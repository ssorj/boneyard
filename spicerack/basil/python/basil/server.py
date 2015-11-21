from qmf.console import *
from wooly import Application
from wooly.server import WebServer

from model import BasilModel
from page import BasilPage

class BasilServer(WebServer):
    def authorized(self, session):
        return True

class BasilApplication(Application):
    def __init__(self):
        super(BasilApplication, self).__init__()

        self.model = BasilModel()
        self.model.add_broker_url("amqp://mrg31.lab.bos.redhat.com")

        self.main_page = BasilPage(self, "index.html")

        self.add_page(self.main_page)
        self.set_default_page(self.main_page)

        self.add_resource_dir("/home/boston/jross/local/mgmt/cumin/instance/resources-wooly") # XXX

    def init(self):
        super(BasilApplication, self).init()

        self.model.init()

    def start(self):
        self.model.start()

    def stop(self):
        self.model.stop()
