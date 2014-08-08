#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import json

data = json.load(open("../../osmef/data.json"))

N = 6
MS = 10

xpoints = (1, 5, 10, 15, 20, 25, 30, 35, 40, 50)
#xpoints = (1, 10, 20, 30, 50)

def calc_jain(values):
    return (sum(values)**2)/(len(values)*sum(values**2))

fig = plt.figure()
ax = fig.add_subplot(111)
lines = []

measures = [('localhost_jain', "o-"), ('vm_localhost_jain', "*-"), ('vm_localhost_4cpu_jain', "^-"), ('vm_localhost_8cpu_jain', "s-"), ('vm_localhost_16cpu_jain', "v-")]
#measures = ['localhost', 'vm_localhost', 'vm_localhost_4cpu']

for m, marker in measures:
    btc_data = []
    for c in xpoints:
        btc_data.append(data[m]["c=%d"%c]["rx.rate_MBps"]["per_connection"])

    jain_indexes = []
    for d in btc_data:
        d = np.array([ float(x) for x in d ])
        jain_indexes.append(calc_jain(d))

    lines.append(ax.plot(xpoints, jain_indexes, marker, markersize=MS))

legend = ["PHY", "1 VCPU", "4 VCPU", "8 VCPU", "16 VCPU"]

# add some
ax.set_ylim(bottom=0, top=1)
ax.set_xlabel('Concurrent connections')
#ax.set_ylabel('BTC in MB/s')
ax.set_title("Jain's index for localhost connections")
#ax.set_xticks(ind+width)
#ax.set_xticklabels([ str(x) for x in xpoints ])
ax.grid(True)

ax.legend([x[0] for x in lines], legend, loc="lower left")

#fig.autofmt_xdate()

plt.savefig("jain_localhost.pdf")

