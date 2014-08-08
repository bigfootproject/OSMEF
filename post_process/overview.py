#!/usr/bin/python

import json
import sys
import os

summary = {}
for f in sys.argv[1:]:
    data = json.load(open(f, "r"))
    scen_name = os.path.split(f)[-1][:-len("_summary.json")]
    summary[scen_name] = {}
    summary[scen_name]["thr"] = data[scen_name]["aggr"]["total_throughput_bit_sec"]["thr"]
    summary[scen_name]["std"] = data[scen_name]["aggr"]["total_throughput_bit_sec"]["std"]

print("Results")

print("{:<20s} | {:>8s} | {:>8s}".format("scenario", "aggregate thrput Gbit/s", "stddev"))

for name in sorted(summary):
    print("{:<20s} | {:>8.3f} | {:>8.3f}".format(name, float(summary[name]["thr"]) / 1000000000, float(summary[name]["std"]) / 1000000000))

