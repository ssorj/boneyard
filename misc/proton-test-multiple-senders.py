#!/usr/bin/python

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

class Handler(MessagingHandler):
    def on_start(self, event):
        self.conn = event.container.connect("localhost:56720")
        self.sender_1 = event.container.create_sender(self.conn, "simple_queue")
        self.sender_2 = event.container.create_sender(self.conn, "simple_queue")

        self.sent = 0
        self.accepted = 0

    def on_sendable(self, event):
        if self.sent < 10:
            print(event, event.sender.name)
            event.sender.send(Message("AAA"))
            self.sent += 1

    def on_accepted(self, event):
        print(event, event.delivery.tag)
        self.accepted += 1

        if self.accepted == 10:
            self.conn.close()
        
container = Container(Handler())
container.run()
