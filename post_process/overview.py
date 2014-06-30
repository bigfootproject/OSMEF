#!/usr/bin/python

import json
import sys

summary = {}
for f in sys.argv[1:]:
    data = json.load(open(f, "r"))
    summary[data.keys()[0]] = {}
    summary[data.keys()[0]]["thr"] = data[data.keys()[0]]["aggr"]["total_throughput_bit_sec"]["thr"]
    summary[data.keys()[0]]["std"] = data[data.keys()[0]]["aggr"]["total_throughput_bit_sec"]["std"]

print("Results")

print("{:<20s} | {:>8s} | {:>8s}".format("scenario", "aggregate thrput Gbit/s", "stddev"))

for name in sorted(summary):
    print("{:<20s} | {:>8.3f} | {:>8.3f}".format(name, float(summary[name]["thr"]) / 1000000000, float(summary[name]["std"]) / 1000000000))

