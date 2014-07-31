#!/usr/bin/python

import os
import matplotlib.pyplot as plt
import numpy as np
import sys

import utils

exp = {
    'vms_on_same_host_v2': range(2, 51),
}
exp_names = {
    'vms_on_same_host_v2': '10 GB',
}

summary = {}

for e in exp:
    summary[e] = {}
    for s in exp[e]:
        data = utils.load_experiments("local%d" % s, e)
        bw_exps = []
        for d in data:
            bw_exps.append(utils.exp_calc_bw(d))
        summary[e]["local%d" % s] = {}
        summary[e]["local%d" % s]["thr"] = np.average(bw_exps)
        summary[e]["local%d" % s]["std"] = np.std(bw_exps)
        print(bw_exps)

MS = 8  # markersize

fig, ax = plt.subplots()
lines = []

for e in exp:
    btc_data = []
    err_data = []
    for s in exp[e]:
        btc_data.append(summary[e]["local%d" % s]["thr"] / 1000000000)
        err_data.append(summary[e]["local%d" % s]["std"] / 1000000000)

    lines.append(ax.plot(exp[e], btc_data, "o-", markersize=MS))
    ax.errorbar(exp[e], btc_data, yerr=err_data, linestyle="None", marker="None")

legend = [ exp_names[x] for x in exp ]

# add some
ax.set_xlabel('Number of VMs')
ax.set_ylabel('Aggregated throughput Gbit/s')
ax.set_title('Same host throughput')
#ax.set_xticks(ind+width)
#ax.set_xticklabels([ str(x) for x in xpoints ])
ax.grid(True)

ax.legend([x[0] for x in lines], legend, loc=8)

#fig.autofmt_xdate()

#plt.savefig("same_thrput.pdf")
plt.tight_layout()
plt.show()
