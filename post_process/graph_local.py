#!/usr/bin/python

import os
import numpy as np
import matplotlib.pyplot as plt
import json

summary = {}

series_10gb_dir = "../experiments/vms_on_same_host"
series_1tb_dir = "../experiments/vms_on_same_host_1tb"

summary["10 GB"] = {}
summary["1 TB"] = {}

for f in os.listdir(series_10gb_dir):
    if "_summary.json" in f:
        data = json.load(open(f, "r"))
        summary["10 GB"][data.keys()[0]] = {}
        summary["10 GB"][data.keys()[0]]["thr"] = data[data.keys()[0]]["aggr"]["total_throughput_bit_sec"]["thr"]
        summary["10 GB"][data.keys()[0]]["std"] = data[data.keys()[0]]["aggr"]["total_throughput_bit_sec"]["std"]

for f in os.listdir(series_1tb_dir):
    if "_summary.json" in f:
        data = json.load(open(f, "r"))
        summary["1 TB"][data.keys()[0]] = {}
        summary["1 TB"][data.keys()[0]]["thr"] = data[data.keys()[0]]["aggr"]["total_throughput_bit_sec"]["thr"]
        summary["1 TB"][data.keys()[0]]["std"] = data[data.keys()[0]]["aggr"]["total_throughput_bit_sec"]["std"]

MS = 10  # markersize

fig = plt.figure()
ax = fig.add_subplot(111)
lines = []

xpoints = range(2, 30)
btc_data = []
for c in xpoints:
    btc_data.append(summary["10 GB"]["local%d" % c]["thr"] / 1000000000)
print(btc_data)

lines.append(ax.plot(xpoints, btc_data, "o-", markersize=MS))

xpoints = range(2, 20)
btc_data = []
for c in xpoints:
    btc_data.append(summary["1 TB"]["local%d_1tb" % c]["thr"] / 1000000000)

lines.append(ax.plot(xpoints, btc_data, "v-", markersize=MS))

legend = ["10 GB", "1 TB"]

# add some
ax.set_xlabel('Number of VMs')
ax.set_ylabel('Aggregated throughput')
ax.set_title('Same host throughput')
#ax.set_xticks(ind+width)
#ax.set_xticklabels([ str(x) for x in xpoints ])
ax.grid(True)

ax.legend([x[0] for x in lines], legend, loc=7)

#fig.autofmt_xdate()

plt.savefig("same_thrput.pdf")

