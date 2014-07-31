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
    if scen.get("description", "name") + "-" not in d:
        continue
    experiments.append(d)

print("Found %d experiments for this scenario" % len(experiments))

all_good = True

shuffle_size = int(scen.get("description", "total_shuffle_size")) * 1024 * 1024 * 1024
for d in experiments:
    total_map_count = 0
    total_red_count = 0

    data = json.load(open(os.path.join(d, "summary.json")))
    if (len(data) != num_vms):
        print("(%s) Expected %d VMs, found %d" % (d, num_vms, len(data)))
        all_good = False
    for i in range(num_vms):
        vm = "vm%d" % (i + 1)
        map_cnt = int(scen.get(vm, "num_mappers"))
        total_map_count += map_cnt
        for m in range(map_cnt):
            mapn = "%s:m%d" % (vm, m)
            try:
                data[vm][mapn]
            except KeyError:
                all_good = False
                print("(%s) Expected mapper %s, not found" % (d, mapn))
        red_cnt = int(scen.get(vm, "num_reducers"))
        total_red_count += red_cnt
        for r in range(red_cnt):
            redn = "%s:r%d" % (vm, r)
            try:
                data[vm][redn]
            except KeyError:
                all_good = False
                print("(%s) Expected reducer %s, not found" % (d, mapn))

    per_mapper_size = shuffle_size / total_map_count
    per_reducer_size = per_mapper_size / total_red_count
    per_reducer_size += 1  # There is also the termination byte

    for i in range(num_vms):
        for m in range(map_cnt):
            for conn in data[vm][mapn]:
                if int(conn["bytes"]) != int(per_reducer_size):
                    all_good = False
                    print("(%s) %s has moved %s bytes instead of %d" % (d, redn, conn["bytes"], per_reducer_size))
    for r in range(red_cnt):
            for conn in data[vm][redn]:
                if int(conn["bytes"]) != int(per_reducer_size):
                    all_good = False
                    print("(%s) %s has moved %s bytes instead of %d" % (d, redn, conn["bytes"], per_reducer_size))

#        print(data[vm].keys())

if all_good:
    print("No errors found")
