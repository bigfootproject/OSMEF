#!/usr/bin/python

from osmef.scenario.recursive_dict import new
from osmef.scenario.parser import export
from osmef.scenario.types import BTC_SENDER, BTC_RECEIVER

s = new()

runner = "192.168.46.10"
s[runner]["measure"] = "NetBTC"
s[runner]["type"] = BTC_RECEIVER
s[runner]["incoming_count"] = 2

runner = "192.168.46.11"
s[runner]["measure"] = "NetBTC"
s[runner]["type"] = BTC_SENDER
s[runner]["receivers"] = ["192.168.46.10"] * 2
s[runner]["duration"] = 2  # seconds

export("host_to_host.json", s)

