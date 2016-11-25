#!/usr/bin/python

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import time

from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container
from threading import *
from Queue import Queue, Empty

class Handler(MessagingHandler):
    def __init__(self):
        super(Handler, self).__init__()

        self.started = Event()
    
    def on_start(self, event):
        self.conn = event.container.connect("localhost:56720")

        self.send_requests = Queue()
        
        self.sent = 0
        self.accepted = 0

        event.container.schedule(1, self)

        self.started.set()

    def on_timer_task(self, event):
        while True:
            try:
                send_request = self.send_requests.get(block=False)
            except Empty:
                pass
        
        self.sender_1 = event.container.create_sender(self.conn, "simple_queue")
        self.sender_2 = event.container.create_sender(self.conn, "simple_queue")

        event.container.schedule(1, self)

    def on_sendable(self, event):
        if self.sent < 10:
            print(event, event.sender.name)
            event.sender.send(Message("AAA"))
            self.sent += 1

    def on_accepted(self, event):
        print(event, event.delivery.tag, event.delivery.link)
        self.accepted += 1

        if self.accepted == 10:
            self.conn.close()

class ControlThread(Thread):
    def __init__(self, handler):
        Thread.__init__(self)
        
        self.handler = handler
        self.daemon = True

    def run(self):
        self.handler.started.wait()
        
        self.handler.command_queue.put(
        for i in range(10):
            print("Tick")

handler = Handler()
            
thread = ControlThread(handler)
thread.start()
            
container = Container(handler)
container.run()
