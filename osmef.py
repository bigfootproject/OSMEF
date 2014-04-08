#!/usr/bin/python3

import argparse
import logging
log = logging.getLogger("osmef")
import sys

DEFAULT_PORT = 9999

from osmef.scenario import parser

arg_parser = argparse.ArgumentParser(description='OSMeF runner options')
arg_parser.add_argument('-p', '--port', type=int, help='Port to use for the control connection', default=DEFAULT_PORT)
arg_parser.add_argument('-s', '--scenario', type=str, help='Scenario name, use "list" to have a list of available scenarios')
arg_parser.add_argument('-d', '--not-delete', help='Do not delete the VMs at the end of the measurement', action="store_true")

args = arg_parser.parse_args()
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("novaclient").setLevel(logging.INFO)

sm = parser.ScenarioManager()

if args.scenario == "list" or args.scenario not in sm.list_available():
    print("Avaliable scenarios:")
    for s in sm.list_available():
        print("  {}".format(s))
    sys.exit(1)

sm.select(args.scenario)

# ...

if not args.not_delete:
    sm.cleanup()

