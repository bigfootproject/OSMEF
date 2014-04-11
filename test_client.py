#!/usr/bin/python3
import sys
import logging
import osmef.command_proto
import osmef.nodes

if len(sys.argv) < 2:
    print("Usage: {} <IP>".format(sys.argv[0]))
    sys.exit(1)

logging.basicConfig(level=logging.DEBUG)

fake_vm = {"ip": sys.argv[1]}
fake_vm["name"] = "fake_vm"
fake_vm["num_reducers"] = 0
fake_vm["num_mappers"] = 2
fake_vm["mappers"] = []
fake_vm["reducers"] = []

n = osmef.nodes.Mapper()
n.port = 23330
n.max_incoming_conn = 40
n.ip = "127.0.0.1"
n.reducer_sizes = [1024]
fake_vm["mappers"].append(n)

n = osmef.nodes.Mapper()
n.port = 23331
n.max_incoming_conn = 40
n.ip = "127.0.0.1"
n.reducer_sizes = [1024]
fake_vm["mappers"].append(n)

osmef.command_proto.init([fake_vm])
osmef.command_proto.end([fake_vm])
