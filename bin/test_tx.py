#!/usr/bin/python3

import socket
import sys

DATA_SIZE = 1024 * 1024 * 1024
BUFFER_SIZE = 65536
HOST, PORT = sys.argv[1], 9998

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

data_sent = 0
cnt = 0
buf = bytearray(BUFFER_SIZE)
byte_cnt = BUFFER_SIZE - 1
while byte_cnt >= 0:
    buf[byte_cnt] = cnt & 0x7F
    cnt += 1
    cnt = cnt % 256
    byte_cnt -= 1

while data_sent < DATA_SIZE:
    sock.sendall(buf)
    data_sent += BUFFER_SIZE

sock.close()

print("Sent: {}KB".format(data_sent / 1024))
