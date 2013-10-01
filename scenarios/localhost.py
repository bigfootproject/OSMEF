#!/usr/bin/python

from osmef.scenario.recursive_dict import new
from osmef.scenario.parser import export

s = new()

runner = "127.0.0.1"  # for testing purposes we have the client and the runner on the same host
s[runner]["measure"] = "NetBTCLocalhost"
s[runner]["concurrency"] = 2
s[runner]["duration"] = 2  # seconds

export("localhost.json", s)

