#!/usr/bin/python

import sys
import os
import json

import utils

try:
    scenario_name = sys.argv[1]
    exp_name = sys.argv[2]
except IndexError:
    print("Usage: sanity_checks <scenario> <experiment>")
    sys.exit(1)

print("Checking results against scenario %s" % utils.scen_name(scenario_name))

num_vms = utils.scen_num_vms(scenario_name)

experiments = utils.load_experiments(scenario_name, exp_name)
print("Found %d experiments for this scenario" % len(experiments))

all_good = True

shuffle_size = utils.scen_shuffle_size(scenario_name)
for data in experiments:
    total_map_count = 0
    total_red_count = 0

    if (len(data) != num_vms):
        print("(%s) Expected %d VMs, found %d" % (d, num_vms, len(data)))
        all_good = False
    for i in range(num_vms):
        vm = "vm%d" % (i + 1)
        map_cnt = utils.scen_num_mappers(scenario_name, vm)
        total_map_count += map_cnt
        for m in range(map_cnt):
            mapn = "%s:m%d" % (vm, m)
            try:
                data[vm][mapn]
            except KeyError:
                all_good = False
                print("(%s) Expected mapper %s, not found" % (d, mapn))
        red_cnt = utils.scen_num_reducers(scenario_name, vm)
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
