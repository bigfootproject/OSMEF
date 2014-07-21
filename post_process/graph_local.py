#!/usr/bin/python

import os
import matplotlib.pyplot as plt
import json

summary = {}

series_10gb_dir = "../experiments/vms_on_same_host"
series_1tb_dir = "../experiments/vms_on_same_host_1tb"

summary["10 GB"] = {}
summary["1 TB"] = {}

for f in os.listdir(series_10gb_dir):
    if "_summary.json" in f:
        data = json.load(open(os.path.join(series_10gb_dir, f), "r"))
        summary["10 GB"][list(data.keys())[0]] = {}
        summary["10 GB"][list(data.keys())[0]]["thr"] = data[list(data.keys())[0]]["aggr"]["total_throughput_bit_sec"]["thr"]
        summary["10 GB"][list(data.keys())[0]]["std"] = data[list(data.keys())[0]]["aggr"]["total_throughput_bit_sec"]["std"]

for f in os.listdir(series_1tb_dir):
    if "_summary.json" in f:
        data = json.load(open(os.path.join(series_1tb_dir, f), "r"))
        summary["1 TB"][list(data.keys())[0]] = {}
        summary["1 TB"][list(data.keys())[0]]["thr"] = data[list(data.keys())[0]]["aggr"]["total_throughput_bit_sec"]["thr"]
        summary["1 TB"][list(data.keys())[0]]["std"] = data[list(data.keys())[0]]["aggr"]["total_throughput_bit_sec"]["std"]

MS = 8  # markersize

fig = plt.figure()
ax = fig.add_subplot(111)
lines = []

xpoints = range(2, 35)
btc_data = []
err_data = []
for c in xpoints:
    btc_data.append(summary["10 GB"]["local%d" % c]["thr"] / 1000000000)
    err_data.append(summary["10 GB"]["local%d" % c]["std"] / 1000000000)
print(btc_data)

lines.append(ax.plot(xpoints, btc_data, "o-", markersize=MS))
ax.errorbar(xpoints, btc_data, yerr=err_data, linestyle="None", marker="None")

xpoints = range(2, 40)
btc_data = []
err_data = []
for c in xpoints:
    btc_data.append(summary["1 TB"]["local%d_1tb" % c]["thr"] / 1000000000)
    err_data.append(summary["1 TB"]["local%d_1tb" % c]["std"] / 1000000000)

lines.append(ax.plot(xpoints, btc_data, "v-", markersize=MS))
ax.errorbar(xpoints, btc_data, yerr=err_data, linestyle="None", marker="None")

legend = ["10 GB", "1 TB"]

# add some
ax.set_xlabel('Number of VMs')
ax.set_ylabel('Aggregated throughput Gbit/s')
ax.set_title('Same host throughput')
#ax.set_xticks(ind+width)
#ax.set_xticklabels([ str(x) for x in xpoints ])
ax.grid(True)

ax.legend([x[0] for x in lines], legend, loc=8)

#fig.autofmt_xdate()

plt.savefig("same_thrput.pdf")

