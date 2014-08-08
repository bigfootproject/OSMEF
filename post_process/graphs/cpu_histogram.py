#!/usr/bin/python

import numpy as np
import matplotlib.pyplot as plt
import json

data = json.load(open("../../osmef/data.json"))

N = 10

rxMeans = []
rxMeans.append(data["localhost"]["c=1"]["rx.cpu"]["avg"])
rxMeans.append(data["vm_localhost"]["c=1"]["rx.cpu"]["avg"])
rxMeans.append(data["vm_host"]["c=1"]["rx.cpu"]["avg"])
rxMeans.append(data["host_vm"]["c=1"]["rx.cpu"]["avg"])
rxMeans.append(data["host_to_host"]["c=1"]["rx.cpu"]["avg"])
rxMeans.append(data["host_to_host_gre"]["c=1"]["rx.cpu"]["avg"])
rxMeans.append(data["vm_to_vm_1"]["c=1"]["rx.cpu"]["avg"])
rxMeans.append(data["vm_to_vm_2"]["c=1"]["rx.cpu"]["avg"])
rxMeans.append(data["vm_to_vm_3"]["c=1"]["rx.cpu"]["avg"])
rxMeans.append(data["vm_to_vm_4"]["c=1"]["rx.cpu"]["avg"])

rxStd = []
rxStd.append(data["localhost"]["c=1"]["rx.cpu"]["std"])
rxStd.append(data["vm_localhost"]["c=1"]["rx.cpu"]["std"])
rxStd.append(data["vm_host"]["c=1"]["rx.cpu"]["std"])
rxStd.append(data["host_vm"]["c=1"]["rx.cpu"]["std"])
rxStd.append(data["host_to_host"]["c=1"]["rx.cpu"]["std"])
rxStd.append(data["host_to_host_gre"]["c=1"]["rx.cpu"]["std"])
rxStd.append(data["vm_to_vm_1"]["c=1"]["rx.cpu"]["std"])
rxStd.append(data["vm_to_vm_2"]["c=1"]["rx.cpu"]["std"])
rxStd.append(data["vm_to_vm_3"]["c=1"]["rx.cpu"]["std"])
rxStd.append(data["vm_to_vm_4"]["c=1"]["rx.cpu"]["std"])

ind = np.arange(N)  # the x locations for the groups
width = 0.35       # the width of the bars

fig = plt.figure()
ax = fig.add_subplot(111)
rects1 = ax.bar(ind, rxMeans, width, color='r', yerr=rxStd)

txMeans = []
txMeans.append(data["localhost"]["c=1"]["tx.cpu"]["avg"])
txMeans.append(data["vm_localhost"]["c=1"]["tx.cpu"]["avg"])
txMeans.append(data["vm_host"]["c=1"]["tx.cpu"]["avg"])
txMeans.append(data["host_vm"]["c=1"]["tx.cpu"]["avg"])
txMeans.append(data["host_to_host"]["c=1"]["tx.cpu"]["avg"])
txMeans.append(data["host_to_host_gre"]["c=1"]["tx.cpu"]["avg"])
txMeans.append(data["vm_to_vm_1"]["c=1"]["tx.cpu"]["avg"])
txMeans.append(data["vm_to_vm_2"]["c=1"]["tx.cpu"]["avg"])
txMeans.append(data["vm_to_vm_3"]["c=1"]["tx.cpu"]["avg"])
txMeans.append(data["vm_to_vm_4"]["c=1"]["tx.cpu"]["avg"])

txStd = []
txStd.append(data["localhost"]["c=1"]["tx.cpu"]["std"])
txStd.append(data["vm_localhost"]["c=1"]["tx.cpu"]["std"])
txStd.append(data["vm_host"]["c=1"]["tx.cpu"]["std"])
txStd.append(data["host_vm"]["c=1"]["tx.cpu"]["std"])
txStd.append(data["host_to_host"]["c=1"]["tx.cpu"]["std"])
txStd.append(data["host_to_host_gre"]["c=1"]["tx.cpu"]["std"])
txStd.append(data["vm_to_vm_1"]["c=1"]["tx.cpu"]["std"])
txStd.append(data["vm_to_vm_2"]["c=1"]["tx.cpu"]["std"])
txStd.append(data["vm_to_vm_3"]["c=1"]["tx.cpu"]["std"])
txStd.append(data["vm_to_vm_4"]["c=1"]["tx.cpu"]["std"])

rects2 = ax.bar(ind+width, txMeans, width, color='y', yerr=txStd)

# add some
ax.set_ylabel('CPU usage %')
ax.set_title('CPU usage with 1 connection')
ax.set_xticks(ind+width)
ax.set_xticklabels( ('localhost', 'VM localhost', 'VM to host', 'host to VM', 'host to host', 'host to host GRE', 'VM to VM 1', 'VM to VM 2', 'VM to VM 3', 'VM to VM 4') )

ax.legend( (rects1[0], rects2[0]), ('Receiver', 'Transmitter') )

#def autolabel(rects):
#    # attach some text labels
#    for rect in rects:
#        height = rect.get_height()
#        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
#                ha='center', va='bottom')
#
#autolabel(rects1)
#autolabel(rects2)

fig.autofmt_xdate()

plt.savefig("cpu_histogram.pdf")

