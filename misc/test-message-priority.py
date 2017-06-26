#!/usr/bin/python

import time

from qpid_messaging import *

def main():
    conn = Connection("127.0.0.1:5672", protocol=b"amqp1.0", sasl_mechanisms=b"ANONYMOUS")
    conn.open()

    try:
        session = conn.session()
        sender = session.sender("q0")

        m1 = Message("m1p2")
        m2 = Message("m2p3")
        m3 = Message("m3p1")

        m1.priority = 2
        m2.priority = 3
        m3.priority = 1

        for m in [m1, m2, m3]:
            sender.send(m)
            print("Sent {}".format(m))

        time.sleep(2)

        receiver = session.receiver("q0")
        receiver.capacity = 3

        for i in range(3):
            print("Received {}".format(receiver.get()))

        session.acknowledge()
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
