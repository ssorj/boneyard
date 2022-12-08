#!/usr/bin/python

import socket
import threading

def run(conn):
    with conn:
        while True:
            # print(111)

            data = conn.recv(16384)

            # print(222, data[:20])

            if not data:
                break

            conn.send(data)

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("localhost", 45674))
        sock.listen(5)

        while True:
            conn, addr = sock.accept()
            threading.Thread(target=run, args=[conn]).start()
    finally:
        sock.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
