#!/usr/bin/python

import json
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm

#KEY = "cpu_time"
#KEY = "bytes"
KEY = "time_elapsed"
POV = "r"  # point of view: mapper (m) or reducer (r)

title = "%s as recorded by the %s" % (KEY, "mappers" if POV is "m" else "reducers")

data = json.load(open(sys.argv[1]))

num_vms = 0
num_nodes_per_vm = 1

peers = []
for vm in data:
    num_vms += 1
    for n in data[vm].keys():
        if ":" + POV in n:
            peers.append(n)

values = {}
for peer in peers:
    for vm in data:
        for n in data[vm].keys():
            if ":" + POV not in n:
                for conn in data[vm][n]:
#                    print(peer, n, conn["peer_name"])
                    if peer == conn["peer_name"]:
                        values[(peer, n)] = conn[KEY]

keys = sorted(list(values.keys()))
print(keys)

def getindex(k):
    m = re.match(r"vm([0-9]+):[mr]([0-9]+)", k)
    return int(m.group(1)) + int(m.group(2)) - 1

matrix = np.zeros((len(peers), len(peers)))
xlabels = [""] * len(peers)
ylabels = [""] * len(peers)
for k in keys:
    x = getindex(k[0])
    y = getindex(k[1])
    matrix[x, y] = values[k]
    xlabels[x] = k[0]
    ylabels[y] = k[1]

print(matrix)

fig, ax = plt.subplots()

cax = ax.pcolor(matrix, cmap=cm.jet)
ax.set_title(title, y=1.18)
plt.xlim(0,len(xlabels))
plt.ylim(0,len(ylabels))
ax.invert_yaxis()
ax.xaxis.tick_top()
ax.set_xticks(np.arange(matrix.shape[1]) + 0.5, minor=False)
ax.set_yticks(np.arange(matrix.shape[0]) + 0.5, minor=False)
ax.set_xticklabels(xlabels)
ax.set_yticklabels(ylabels)
plt.xticks(rotation=90)

# Add colorbar, make sure to specify tick locations to match desired ticklabels
cbar = fig.colorbar(cax, ticks=[np.amin(matrix), np.average(matrix), np.amax(matrix)])
cbar.ax.set_yticklabels(["%d (min)" % np.amin(matrix), "%d (avg)" % np.average(matrix), "%d (max)" % np.amax(matrix)])

plt.tight_layout()
plt.show()
