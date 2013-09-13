#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import json

data = json.load(open("../../osmef/data.json"))

N = 6

xpoints = (1, 5, 10, 20, 30, 50)

fig = plt.figure()
ax = fig.add_subplot(111)
lines = []

btc_data = []
for c in xpoints:
    btc_data.append(data["vm_to_vm_4cpu_1"]["c=%d"%c]["rx.rate_MBps"]["sum"])

lines.append(ax.plot(xpoints, btc_data, "o-"))

btc_data = []
for c in xpoints:
    btc_data.append(data["vm_to_vm_4cpu_2"]["c=%d"%c]["rx.rate_MBps"]["sum"])

lines.append(ax.plot(xpoints, btc_data, "+-"))

btc_data = []
for c in xpoints:
    btc_data.append(data["vm_to_vm_4cpu_3"]["c=%d"%c]["rx.rate_MBps"]["sum"])

lines.append(ax.plot(xpoints, btc_data, "*-"))

btc_data = []
for c in xpoints:
    btc_data.append(data["vm_to_vm_4cpu_4"]["c=%d"%c]["rx.rate_MBps"]["sum"])

lines.append(ax.plot(xpoints, btc_data, "--"))

legend = ["same host same tenant", "diff host same tenant", "same host diff tenant", "diff host diff tenant"]

# add some
ax.set_xlabel('VM to VM concurrent connections')
ax.set_ylabel('BTC in MB/s')
ax.set_title('VM to VM BTC with 4 VCPUs')
#ax.set_xticks(ind+width)
#ax.set_xticklabels([ str(x) for x in xpoints ])
ax.grid(True)

ax.legend([x[0] for x in lines], legend, loc=7)

#fig.autofmt_xdate()

plt.savefig("vm2vm_4cpu_btc.pdf")

