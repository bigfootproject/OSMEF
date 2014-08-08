#!/usr/bin/python3

import socketserver
import time


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        bytes_read = 0
        time_start = time.time()
        while True:
            self.data = self.request.recv(65536)
            if not self.data:
                break
            bytes_read += len(self.data)
        interval = time.time() - time_start
        print("Read: {} MB in {:.2f} seconds ({:.2f} Mbit/s)".format(bytes_read / 1024 / 1024, interval, ((bytes_read * 8) / interval) / 1000000))

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 9998

    server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)

    print("Waiting for incoming connection")
    server.serve_forever()
