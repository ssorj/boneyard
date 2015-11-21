#!/usr/bin/env python

from __future__ import print_function

from proton import Message
from proton.spin import SpinContainer

with SpinContainer():
    conn = container.create_connection("localhost:5672")
    receiver = conn.create_receiver("examples")
    sender = conn.create_sender("examples")

    msg1 = Message("Hello World!")

    sender.send(msg1)

    msg2 = receiver.receive() # => ReceivedMessage

    print(msg2.body)

    msg2.accept()             # ReceivedMessage.accept()

    # All resource cleanup (conn.close()) happens on container exit
