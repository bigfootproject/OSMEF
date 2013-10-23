#!/usr/bin/python
import logging
log = logging.getLogger(__name__)

import osmef.runner
from osmef.client import osmef_run
from osmef.scenario import NetBTCScenario

SSH_USER = "venzano"
SSH_KEY = "~/.ssh/osmef.key"

## Runner 1
r1 = osmef.runner.HostRunner("r1", NetBTCScenario)

config = {}
config["ip"] = "192.168.46.10"
config["ssh_user"] = SSH_USER
config["ssh_key"] = SSH_KEY
config["role"] = osmef.runner.BTC_RECEIVER
config["incoming_count"] = 2
r1.set_config(config)

## Runner 2
r2 = osmef.runner.HostRunner("r2", NetBTCScenario)

config = {}
config["ip"] = "192.168.46.11"
config["role"] = osmef.runner.BTC_SENDER
config["ssh_user"] = SSH_USER
config["ssh_key"] = SSH_KEY
config["receivers"] = ["192.168.46.10"] * 2
config["duration"] = 2  # seconds
r2.set_config(config)

## Start!
scenario = [r1, r2]
results = osmef_run(scenario)

# TODO temporary...
import pprint
pprint.pprint(results)

