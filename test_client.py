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
fake_vm["num_reducers"] = 1
fake_vm["num_mappers"] = 2
fake_vm["mappers"] = []
fake_vm["reducers"] = []

m1 = osmef.nodes.Mapper()
m1.name = "vm1:m0"
m1.port = 23330
m1.max_incoming_conn = 40
m1.ip = "127.0.0.1"
fake_vm["mappers"].append(m1)

m2 = osmef.nodes.Mapper()
m2.name = "vm1:m1"
m2.port = 23331
m2.max_incoming_conn = 40
m2.ip = "127.0.0.1"
fake_vm["mappers"].append(m2)

r1 = osmef.nodes.Reducer()
r1.name = "vm1:r0"
r1.max_outgoing_connections = 1
r1.data_size = 4096
fake_vm["reducers"].append(r1)

m1.all_reducers = [r1]
m2.all_reducers = [r1]
r1.all_mappers = [m1, m2]

osmef.command_proto.init([fake_vm])
osmef.command_proto.start_measurement([fake_vm])
osmef.command_proto.end([fake_vm])
