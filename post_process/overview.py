#!/usr/bin/python

import json
import sys

summary = {}
for f in sys.argv[1:]:
    data = json.load(open(f, "r"))
    summary[data.keys()[0]] = data[data.keys()[0]]["aggr"]["total_throughput_bit_sec"]

print("Results")

print("{:<20s} | {:>8s}".format("scenario", "aggregate thrput Gbit/s"))

for name in sorted(summary):
    print("{:<20s} | {:>8.3f}".format(name, float(summary[name]) / 1000000000))

