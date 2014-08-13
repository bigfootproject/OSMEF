#!/usr/bin/python3

import sys
import numpy as np

import utils

names, data = utils.load_experiments(sys.argv[1], sys.argv[2])

bws = []
for exp in data:
    bws.append(utils.exp_calc_bw(exp))

print("Results")

avg = np.average(bws)
std = np.std(bws)

print("Avg: {:.3f} Gb/s, stddev: {:.3f}".format(avg / 1000000000, std / 1000000000))
#print("{:<20s} | {:>8s} | {:>8s}".format("scenario", "aggregate thrput Gbit/s", "stddev"))

#for name in sorted(summary):
#    print("{:<20s} | {:>8.3f} | {:>8.3f}".format(name, float(summary[name]["thr"]) / 1000000000, float(summary[name]["std"]) / 1000000000))

