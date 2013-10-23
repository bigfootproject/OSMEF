#!/usr/bin/python

import argparse
import logging
import json

from osmef import deploy, run, end

log = logging.getLogger(__name__)

arg_parser = argparse.ArgumentParser(description='OSMeF client')
arg_parser.add_argument('--out_dir', default=".", help="output directory for json files, default is .")
arg_parser.add_argument('-d', '--debug', help='enable debug output', action="store_true")
arg_parser.add_argument('-n', '--name', help="name of the measurement")

args = arg_parser.parse_args()


def osmef_run(scenario, repeat=1):
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    results = {}
    deploy(scenario)
    for count in range(repeat):
        results["run_%d" % count] = run(scenario)
    end(scenario)

    if "name" in vars(args):
        results["name"] = args.name

    return emit_output(results)


def emit_output(out):
    return json.dumps(out, sort_keys=True, indent=4, separators=(',', ': '))

