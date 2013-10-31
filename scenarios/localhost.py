#!/usr/bin/python
import logging
log = logging.getLogger(__name__)
import os, sys
sys.path += [os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))]

import osmef.runner
from osmef.client import osmef_run
from osmef.scenario import NetBTCLocalhostScenario

SSH_USER = "venzano"
SSH_KEY = "/home/venzano/.ssh/osmef.key"

## Runner
r1 = osmef.runner.HostRunner("runner_localhost", NetBTCLocalhostScenario)

config = {}
config["ip"] = "192.168.46.10"
config["ssh_user"] = SSH_USER
config["ssh_key"] = SSH_KEY
config["concurrency"] = 2
config["duration"] = 2
r1.set_config(config)

## Start!
scenario = [r1]
results = osmef_run(scenario)

# TODO temporary...
print(results)

