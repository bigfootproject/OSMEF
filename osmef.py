#!/usr/bin/python3

import argparse
import logging
log = logging.getLogger("osmef")
import time
import sys
import os

DEFAULT_PORT = 9999

from osmef.scenario import parser
import osmef.logs

arg_parser = argparse.ArgumentParser(description='OSMeF runner options')
arg_parser.add_argument('-p', '--port', type=int, help='Port to use for the control connection', default=DEFAULT_PORT)
arg_parser.add_argument('-s', '--scenario', type=str, help='Scenario name, use "list" to have a list of available scenarios')
arg_parser.add_argument('-d', '--not-delete', help='Do not delete the VMs at the end of the measurement', action="store_true")
arg_parser.add_argument('-o', '--output-dir', help='Output directory where results will be stored', default=".")
arg_parser.add_argument('-l', '--logs', help='Save the worker logs for debugging', action="store_true")
arg_parser.add_argument('-r', '--repeat', help='Number of times to repeat the experiment', default=1)

args = arg_parser.parse_args()
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("novaclient").setLevel(logging.INFO)
logging.getLogger("osmef.ssh").setLevel(logging.DEBUG)

for c in range(int(args.repeat)):
    sm = parser.ScenarioManager()

    if args.scenario == "list" or args.scenario not in sm.list_available():
        print("Avaliable scenarios:")
        for s in sm.list_available():
            print("  {}".format(s))
        sys.exit(1)

    out_dir = os.path.join(os.path.abspath(args.output_dir), args.scenario + "-%d" % time.time())
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    ret = sm.select(args.scenario)
    if ret:
        ret = sm.start()
        if not ret:
            log.error("Error while execution scenario")

    logs = sm.scenario_end()
    if args.logs:
        for k in logs:
            fname = os.path.join(out_dir, k + ".log")
            open(fname, "w").write(logs[k])
    json_data = osmef.logs.parse(logs)
    fname = os.path.join(out_dir, "summary.json")
    open(fname, "w").write(json_data)

if not args.not_delete:
    sm.cleanup()

