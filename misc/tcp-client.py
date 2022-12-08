#!/usr/bin/python

import socket
import sys
import threading

def run(thread_id):
    #send_data = b"x" * 65536
    #send_data = b"x" * 32768
    send_data = b"x" * 16384
    #send_data = b"x" * 16387
    #send_data = b"x" * (16384 + 4097)
    #send_data = b"x" * 8192
    #send_data = b"x" * 4096
    total = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect(("localhost", 45673))

    with open(f"transfers.{thread_id}.csv", "w") as transfers:
        with sock:
            while True:
                sent = sock.send(send_data)

                received_data = sock.recv(len(send_data))

                if not received_data:
                    break

                total += len(received_data)
                transfers.write(f"{sent},{len(received_data)},{total}\n")

def main():
    jobs = int(sys.argv[1])

    for i in range(jobs):
        threading.Thread(target=run, args=[i]).start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
