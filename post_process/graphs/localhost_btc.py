#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import json

data = json.load(open("../../osmef/data.json"))

N = 6
MS=10 # markersize

xpoints = (1, 5, 10, 20, 30, 50)

fig = plt.figure()
ax = fig.add_subplot(111)
lines = []

btc_data = []
for c in xpoints:
    btc_data.append(data["localhost"]["c=%d"%c]["rx.rate_MBps"]["sum"])
print(btc_data)
#ind = np.arange(N)  # the x locations for the groups

lines.append(ax.plot(xpoints, btc_data, "o-", markersize=MS))

btc_data = []
for c in xpoints:
    btc_data.append(data["vm_localhost_16cpu"]["c=%d"%c]["rx.rate_MBps"]["sum"])

lines.append(ax.plot(xpoints, btc_data, "v-", markersize=MS))

btc_data = []
for c in xpoints:
    btc_data.append(data["vm_localhost_8cpu"]["c=%d"%c]["rx.rate_MBps"]["sum"])

lines.append(ax.plot(xpoints, btc_data, "s-", markersize=MS))

btc_data = []
for c in xpoints:
    btc_data.append(data["vm_localhost_4cpu"]["c=%d"%c]["rx.rate_MBps"]["sum"])

lines.append(ax.plot(xpoints, btc_data, "^-", markersize=MS))

btc_data = []
for c in xpoints:
    btc_data.append(data["vm_localhost"]["c=%d"%c]["rx.rate_MBps"]["sum"])

lines.append(ax.plot(xpoints, btc_data, "*-", markersize=MS))

#btc_data = []
#for c in xpoints:
#    btc_data.append(data["vm_localhost_32cpu_jain"]["c=%d"%c]["rx.rate_MBps"]["sum"])

#lines.append(ax.plot(xpoints, btc_data, "+-", markersize=MS))


legend = ["PHY", "16 VCPU", "8 VCPUs", "4 VCPUs", "1 VCPUs"]

# add some
ax.set_xlabel('Localhost concurrent connections')
ax.set_ylabel('BTC in MB/s')
ax.set_title('Localhost BTC')
#ax.set_xticks(ind+width)
#ax.set_xticklabels([ str(x) for x in xpoints ])
ax.grid(True)

ax.legend([x[0] for x in lines], legend, loc=7)

#fig.autofmt_xdate()

plt.savefig("localhost_btc.pdf")

