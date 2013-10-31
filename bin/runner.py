#!/usr/bin/python

import argparse
import logging
log = logging.getLogger("runner")
import os
import sys
osmef_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path += [osmef_dir]

from osmef.command_protocol import run_server, DEFAULT_PORT

arg_parser = argparse.ArgumentParser(description='OSMeF runner options')
arg_parser.add_argument('-p', '--port', type=int, help='Port to listen to for incoming control connections', default=DEFAULT_PORT)

args = arg_parser.parse_args()
logging.basicConfig(level=logging.DEBUG, filename=os.path.join(osmef_dir, "runner.log"), filmode="w")

run_server(args.port)

