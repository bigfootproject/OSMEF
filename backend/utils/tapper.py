#!/usr/bin/python

from pytun import TunTapDevice, IFF_TAP
import select
import sys

tap1 = TunTapDevice(flags=IFF_TAP, name="tap1")
tap2 = TunTapDevice(flags=IFF_TAP, name="tap2")

p = select.poll()
p.register(tap1)
p.register(tap2)

while True:
    ev = p.poll(1000)
    if len(ev) > 0:
        for fd,e in ev:
            if e == select.POLLIN:
                sys.stdout.write(".")
                fd.read(1)

