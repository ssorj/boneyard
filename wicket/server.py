#!/usr/bin/env python3

import time

from threading import Thread

from tornado.websocket import WebSocketHandler
from tornado.web import Application
from tornado.ioloop import IOLoop


class TestHandler(WebSocketHandler):
    clients = list()

    def open(self):
        print("WebSocket opened")
        self.__class__.clients.append(self)

    def on_message(self, message):
        print("Message: " + message)
        self.write_message("You said " + message)

    def on_close(self):
        print("WebSocket closed")
        self.__class__.clients.remove(self)

    @classmethod
    def send_message(cls, message):
        for client in cls.clients:
            client.write_message(message)
        
class TestThread(Thread):
    def __init__(self, loop):
        super().__init__()

        self.loop = loop
        self.daemon = True
    
    def run(self):
        counter = 0
        
        while True:
            time.sleep(1)

            def callback():
                TestHandler.send_message("Message {}".format(counter))

            self.loop.add_callback(callback)

            counter += 1

if __name__ == "__main__":
    handler = TestHandler

    app = Application([(r"/ws", TestHandler)])
    app.listen(8888)

    loop = IOLoop.current()
    thread = TestThread(loop)

    thread.start()
    loop.start()
