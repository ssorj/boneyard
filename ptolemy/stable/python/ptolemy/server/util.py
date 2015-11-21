from threading import Thread

from ptolemy.util import *

class ServerThread(Thread):
    def __init__(self, server, name):
        super(ServerThread, self).__init__()

        self.server = server
        self.name = name

        self.setDaemon(True)
