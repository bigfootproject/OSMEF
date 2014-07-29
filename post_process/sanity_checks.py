#!/usr/bin/python

import sys
from configparser import ConfigParser
import os
import json

scenario_file = sys.argv[1]

scen = ConfigParser()
scen.read_file(open(scenario_file))
print("Checking results against scenario %s" % scen.get("description", "name"))

num_vms = int(scen.get("description", "num_vms"))

experiments = []
for d in os.listdir("."):
    if not os.path.isdir(d):
        continue
    if scen.get("description", "name") not in d:
        continue
    experiments.append(d)

print("Found %d experiments for this scenario" % len(experiments))

all_good = True

for d in experiments:
    data = json.load(open(os.path.join(d, "summary.json")))
    if (len(data) != num_vms):
        print("(%s) Expected %d VMs, found %d" % (d, num_vms, len(data)))
        all_good = False
    for i in range(num_vms):
        vm = "vm%d" % (i + 1)
        map_cnt = int(scen.get(vm, "num_mappers"))
        for m in range(map_cnt):
            mapn = "%s:m%d" % (vm, m)
            try:
                data[vm][mapn]
            except KeyError:
                all_good = False
                print("(%s) Expected mapper %s, not found" % (d, mapn))
        red_cnt = int(scen.get(vm, "num_reducers"))
        for r in range(red_cnt):
            redn = "%s:r%d" % (vm, r)
            try:
                data[vm][redn]
            except KeyError:
                all_good = False
                print("(%s) Expected reducer %s, not found" % (d, mapn))

#        print(data[vm].keys())

if all_good:
    print("No errors found")
