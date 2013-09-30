#!/usr/bin/python

import json
import os
import sys

if not os.access("data.json", os.F_OK):
    print("Please run aggregate.py first")
    sys.exit(1)

data = json.load(open("data.json", "r"))

print("Results for 1 connection")

print("{:<20s} {:>8s} | {:>7s} | {:>5s} | {:>5s} | {:>5s} | {:>5s}".format("name",
                                                                                       "btc avg",
                                                                                       "btc std",
                                                                                       "cpuRX",
                                                                                       "std",
                                                                                       "cpuTX",
                                                                                       "std"))
for name in sorted(data):
    print("{:<20s} {:>8.2f} | {:>7.2f} | {:>5.2f} | {:>5.2f} | {:>5.2f} | {:>5.2f}".format(name,
                                    data[name]["c=1"]["btc"]["rx"]["rate_KBps"]["avg"], 
                                    data[name]["c=1"]["conn_1"]["btc"]["rx"]["rate_KBps"]["std"],
                                    data[name]["c=1"]["cpu"]["rx"]["avg"],
                                    data[name]["c=1"]["conn_1"]["cpu"]["rx"]["std"],
                                    data[name]["c=1"]["cpu"]["tx"]["avg"],
                                    data[name]["c=1"]["conn_1"]["cpu"]["tx"]["std"],
                                   ))

print("\nResults for 30 connections")

print("{:<20s} {:>8s} | {:>8s} | {:>7s} | {:>5s} | {:>5s} | {:>5s} | {:>5s}".format("name",
                                                                                       "btc sum",
                                                                                       "btc avg",
                                                                                       "btc std",
                                                                                       "cpuRX",
                                                                                       "std",
                                                                                       "cpuTX",
                                                                                       "std"))
for name in sorted(data):
    print("{:<20s} {:>8.2f} | {:>8.2f} | {:>7.2f} | {:>5.2f} | {:>5.2f} | {:>5.2f} | {:>5.2f}".format(name,
                                    data[name]["c=30"]["btc"]["rx"]["rate_KBps"]["sum"], 
                                    data[name]["c=30"]["btc"]["rx"]["rate_KBps"]["avg"], 
                                    data[name]["c=30"]["btc"]["rx"]["rate_KBps"]["std"], 
                                    data[name]["c=30"]["cpu"]["rx"]["avg"],
                                    data[name]["c=30"]["cpu"]["rx"]["std"],
                                    data[name]["c=30"]["cpu"]["tx"]["avg"],
                                    data[name]["c=30"]["cpu"]["tx"]["std"],
                                   ))

