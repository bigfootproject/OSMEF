#!/usr/bin/python2

import argparse
import pprint
import time
import json
import os

from osmef import os_status
from osmef import nuttcp

def do_btc_host_if(args):
    out = {}
    out["type"] = "BTC host through interface"
    out["time"] = time.time()
    out["senders"] = args.client
    out["receiver"] = args.server_listen
    out["receiver_host"] = args.server
    out["concurrent"] = args.concurrent
    if "name" in args:
        out["name"] = args.name
    print("Gathering state for host %s" % args.client)
    out["state_sender"] = os_status.get_status(args.client, False)
    print("Gathering state for host %s" % args.server)
    out["state_sender"] = os_status.get_status(args.server, False)
    out["btc"] = nuttcp.measure_btc_generic([args.server] * args.concurrent, [args.client] * args.concurrent, [args.server_listen] * args.concurrent, args.duration, False)
    emit_output(out, args)

def do_localhost_btc(args):
    out = {}
    out["type"] = "Localhost BTC"
    out["time"] = time.time()
    out["senders"] = args.host
    out["receiver"] = "127.0.0.1"
    out["concurrent"] = args.concurrent
    if "name" in args:
        out["name"] = args.name
    print("Gathering state for host %s" % args.host)
    out["state_sender"] = os_status.get_status(args.host, False)
    print("Measuring localhost BTC on %s" % (args.host,))
    out["btc"] = nuttcp.measure_btc_localhost(args.host, args.concurrent, args.duration)
    emit_output(out, args)

def do_btc(args):
    receiver = args.receiver.split("@")
    out = {}
    out["type"] = "BTC"
    out["time"] = time.time()
    out["senders"] = args.sender
    out["receiver"] = args.receiver
    out["concurrent"] = args.concurrent
    if "name" in args:
        out["name"] = args.name
    print("Gathering state for host %s" % args.sender)
    out["state_sender"] = os_status.get_status(args.sender, args.namespace)
    print("Gathering state for host %s" % args.receiver)
    out["state_receiver"] = os_status.get_status(args.receiver, args.namespace)
    print("Measuring BTC from %s to %s" % (args.sender, args.receiver))
    out["btc"] = nuttcp.measure_btc(args.receiver, [args.sender] * args.concurrent, args.duration, args.namespace)
    emit_output(out, args)

def emit_output(out, args):
    if args.output == "plain":
        pprint.pprint(out)
    elif args.output == "json":
        fname = os.path.join(args.out_dir, "%d_%s.json" % (time.time(), out["type"]))
        fp = file(fname, "w")
        json.dump(out, fp, sort_keys=True, indent=4, separators=(',', ': '))

## Command line argument parsing

arg_parser = argparse.ArgumentParser(description='Define tests')
arg_parser.add_argument('-o', '--output', choices=["json", "plain"], default="plain", help="select output, default is plain")
arg_parser.add_argument('--out_dir', default=".", help="output directory for json files, default is .")
arg_subparsers = arg_parser.add_subparsers(help='sub-command help', title="subcommands")

# parser for the "btc_localhost" command
parser_lobtc = arg_subparsers.add_parser('localhost_btc', help='BTC (Bulk Transfer Capacity) measurement on localhost')
parser_lobtc.add_argument('-d', '--duration', type=int, help='measurement duration in seconds', default=5)
parser_lobtc.add_argument('-n', '--name', help="name of the measurement")
parser_lobtc.add_argument('-c', '--concurrent', help="number of clients that will connect to the server at the same time", default=1, type=int)
parser_lobtc.add_argument('host', type=str, help='receiver IP, must be in the user@ip format')
parser_lobtc.set_defaults(func=do_localhost_btc)

# parser for the "btc" command
parser_btc = arg_subparsers.add_parser('btc', help='BTC (Bulk Transfer Capacity) measurement')
parser_btc.add_argument('-d', '--duration', type=int, help='measurement duration in seconds', default=5)
parser_btc.add_argument('-n', '--name', help="name of the measurement")
parser_btc.add_argument('-N', '--namespace', help="use namespaces instead of connecting to other hosts", action="store_true")
parser_btc.add_argument('-c', '--concurrent', help="number of clients that will connect to the server at the same time", default=1, type=int)
parser_btc.add_argument('receiver', type=str, help='receiver IP, must be in the user@ip format')
parser_btc.add_argument('sender', type=str, help='sender IP, must be in the user@ip format')
parser_btc.set_defaults(func=do_btc)

# parser for the "btc_host_if" command
parser_btc = arg_subparsers.add_parser('btc_host_if', help='BTC (Bulk Transfer Capacity) measurement between hosts through a specific interface')
parser_btc.add_argument('-d', '--duration', type=int, help='measurement duration in seconds', default=5)
parser_btc.add_argument('-n', '--name', help="name of the measurement")
parser_btc.add_argument('-c', '--concurrent', help="number of clients that will connect to the server at the same time", default=1, type=int)
parser_btc.add_argument('server', type=str, help='where to run the server, must be in the user@ip format')
parser_btc.add_argument('server_listen', type=str, help='where the server is listening, e.g. where the client needs to connect to')
parser_btc.add_argument('client', type=str, help='where to run the client, must be in the user@ip format')
parser_btc.set_defaults(func=do_btc_host_if)

args = arg_parser.parse_args()
args.func(args)

