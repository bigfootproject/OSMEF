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
fake_vm["num_reducers"] = 2
fake_vm["num_mappers"] = 2
fake_vm["mappers"] = []
fake_vm["reducers"] = []

for i in range(fake_vm["num_mappers"]):
    m = osmef.nodes.Mapper()
    m.name = "vm1:m%d" % i
    m.port = 23330 + i
    m.max_incoming_conn = 40
    m.ip = "127.0.0.1"
    fake_vm["mappers"].append(m)

for i in range(fake_vm["num_reducers"]):
    r = osmef.nodes.Reducer()
    r.name = "vm1:r%d" % i
    r.max_outgoing_conn = 4
    r.data_size = 20960000
    fake_vm["reducers"].append(r)

for m in fake_vm["mappers"]:
    m.all_reducers = fake_vm["reducers"]

for r in fake_vm["reducers"]:
    r.all_mappers = fake_vm["mappers"]

osmef.command_proto.init([fake_vm])
osmef.command_proto.start_measurement([fake_vm])
osmef.command_proto.end([fake_vm])
