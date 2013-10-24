#!/usr/bin/python

import argparse
import socketserver
import logging
log = logging.getLogger("runner")
import sys, os
sys.path += [os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))]

from osmef.command_protocol import OSMeFProtoHandler, DEFAULT_PORT

arg_parser = argparse.ArgumentParser(description='OSMeF runner options')
arg_parser.add_argument('-p', '--port', type=int, help='Port to listen to for incoming control connections', default=DEFAULT_PORT)
arg_parser.add_argument('-d', '--debug', help='enable debug output', action="store_true")

args = arg_parser.parse_args()
if args.debug:
    logging.basicConfig(level=logging.DEBUG)

socketserver.ThreadingTCPServer.allow_reuse_address = True
server = socketserver.ThreadingTCPServer(("0.0.0.0", args.port), OSMeFProtoHandler)
log.info("Listening on port {0}".format(args.port))
server.serve_forever()

