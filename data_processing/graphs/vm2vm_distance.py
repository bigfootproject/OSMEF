#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import json

data = json.load(open("../../osmef/data.json"))

N = 3
MS = 10 # markersize

xpoints = (0, 2, 4)

fig = plt.figure()
ax = fig.add_subplot(111)
lines = []

btc_data = []
btc_data.append(data["vm_to_vm_1"]["c=1"]["rx.rate_MBps"]["avg"])
btc_data.append(data["vm_to_vm_2"]["c=1"]["rx.rate_MBps"]["avg"])
btc_data.append(data["vm_to_vm_3"]["c=1"]["rx.rate_MBps"]["avg"])
#point = data["vm_to_vm_3"]["c=1"]["rx.rate_MBps"]["avg"]
print(btc_data)
lines.append(ax.semilogy(xpoints, btc_data, "o-", markersize=MS))

btc_data = []
btc_data.append(data["vm_to_vm_1"]["c=10"]["rx.rate_MBps"]["avg"])
btc_data.append(data["vm_to_vm_2"]["c=10"]["rx.rate_MBps"]["avg"])
btc_data.append(data["vm_to_vm_3"]["c=10"]["rx.rate_MBps"]["avg"])

lines.append(ax.semilogy(xpoints, btc_data, "*-", markersize=MS))


btc_data = []
btc_data.append(data["vm_to_vm_1"]["c=30"]["rx.rate_MBps"]["avg"])
btc_data.append(data["vm_to_vm_2"]["c=30"]["rx.rate_MBps"]["avg"])
btc_data.append(data["vm_to_vm_3"]["c=30"]["rx.rate_MBps"]["avg"])

lines.append(ax.semilogy(xpoints, btc_data, "^-", markersize=MS))


btc_data = []
btc_data.append(data["vm_to_vm_1"]["c=50"]["rx.rate_MBps"]["avg"])
btc_data.append(data["vm_to_vm_2"]["c=50"]["rx.rate_MBps"]["avg"])
btc_data.append(data["vm_to_vm_3"]["c=50"]["rx.rate_MBps"]["avg"])

lines.append(ax.semilogy(xpoints, btc_data, "s-", markersize=MS))

#ax.plot(4, point, "^")

legend = ["p = 1", "p = 10", "p = 30", "p = 50"]

# add some
ax.set_title('VM to VM BTC')
ax.set_xlabel('Distance')
ax.set_ylabel('BTC in MB/s')
ax.set_xticks([0, 2, 4])
#ax.set_xbound(-0.5, 4.5)
#ax.set_xticklabels(xpoints)
ax.grid(True)

ax.legend([x[0] for x in lines], legend, loc="upper right")

#fig.autofmt_xdate()

plt.savefig("vm2vm_distance.pdf")

