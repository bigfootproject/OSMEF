#!/usr/bin/python

import sys, os, re
import json
import argparse
import numpy
from pprint import pprint

BASE_DIR="output/paper/"

class NestedDict(dict):
    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, NestedDict())

def filter_measures(data, concurrent):
    """Return a filtered data dictionary containing only the selected concurrent number"""
    out = {}
    for measure in data.keys():
        conc = get_many_values_one_measurement(data[measure], ["concurrent"])[0]
        if conc == concurrent:
            out[measure] = data[measure]
    return out

def find_concurrent_values(data):
    out = []
    for measure in data.keys():
        out.append(get_many_values_one_measurement(data[measure], ["concurrent"])[0])
    return sorted(out)

def get_one_value_many_measurements(measurements, key):
    out = []
    for m in measurements:
        try:
            out.append(dotkey(measurements[m], key))
        except KeyError:
            import traceback
            traceback.print_exc()
            out.append("N/A")
    return out

def get_many_values_one_measurement(measurement, keys):
    out = []
    for key in keys:
        try:
            out.append(dotkey(measurement, key))
        except KeyError:
            import traceback
            traceback.print_exc()
            out.append("N/A")
    return out

def dotkey(tree_root, dotted_key):
    dotted_key = dotted_key.split(".")
    value = tree_root
    for key in dotted_key:
        value = value[key]
    return value

def load_json(fname):
    return json.load(open(fname, "r"))

def load_all(src_dir):
    data = {}
    file_list = os.listdir(src_dir)
    for f in file_list:
        if not os.path.splitext(f)[1] == ".json":
            continue
        if f[0] == "N":
            print("Skipping NOTUSE file")
            continue
        fp = os.path.join(src_dir, f)
        try:
            data[f] = load_json(fp)
        except ValueError:
            print("Skipping corrupted file: %s" % f)
            continue
    return data

def calc(values, fun_pre=lambda x: x, fun_after=lambda x: x):
    values = [ fun_pre(x) for x in values ]
    values = numpy.array(values)
    out = {}
    out["avg"] = fun_after(numpy.average(values))
#    out["sum"] = fun_after(numpy.sum(values))
    out["std"] = fun_after(numpy.std(values))
    return out

def generate_keys(key_template, count):
    out = []
    for idx in range(count):
        out.append(key_template % (idx+1,))
    return out

data = {}

for d in os.listdir(BASE_DIR):
    path = os.path.join(BASE_DIR, d)
    if not os.path.isdir(path):
        continue
    data[d] = {}
    data[d]["raw"] = load_all(path)
    
    # Please remember that for c=1 we are working with 5 samples of the same thing, while for
    # conn=5,10,... we have 1 sample of many connections
    # Weelllll, this is not always true...

    concurrent_values = find_concurrent_values(data[d]["raw"])
    concurrent_values = sorted(list(set(concurrent_values)))

    fun_KBtoMB = lambda x: x/1024
    fun_toFloat = lambda x: float(x.strip())
    fun_perc = lambda x: float(x.strip()[:-1])

    while len(concurrent_values) > 0:
        conc = concurrent_values.pop(0)
        conn_data = filter_measures(data[d]["raw"], conc)
        print("Measure %s has %d sample(s) with conc=%d" % (d, len(conn_data), conc))

        data_aux = NestedDict()
        data[d]["c=%d"%conc] = data_aux

        data_aux["n_samples"] = len(conn_data)
        for c in range(1, conc+1):
            # BTC RX
            samples = get_one_value_many_measurements(conn_data, "btc.conn_%d.rx.rate_KBps"%c)
            data_aux["conn_%d"%c]["btc"]["rx"]["rate_KBps"] = calc(samples, fun_toFloat, fun_KBtoMB)
            data_aux["conn_%d"%c]["btc"]["rx"]["rate_KBps"]["samples"] = [ fun_KBtoMB(float(x)) for x in samples ]

            # CPU RX
            samples = get_one_value_many_measurements(conn_data, "btc.conn_%d.rx.cpu"%c)
            data_aux["conn_%d"%c]["cpu"]["rx"] = calc(samples, fun_perc)
            data_aux["conn_%d"%c]["cpu"]["rx"]["samples"] = [ float(fun_perc(x)) for x in samples ]

            # CPU TX
            samples = get_one_value_many_measurements(conn_data, "btc.conn_%d.tx.cpu"%c)
            data_aux["conn_%d"%c]["cpu"]["tx"] = calc(samples, fun_perc)
            data_aux["conn_%d"%c]["cpu"]["tx"]["samples"] = [ float(fun_perc(x)) for x in samples ]

        # Aggregate BTC
        values = [ data_aux["conn_%d"%c]["btc"]["rx"]["rate_KBps"]["avg"] for c in range(1, conc+1) ]
        data[d]["c=%d"%conc]["btc"]["rx"]["rate_KBps"] = calc(values)
        data[d]["c=%d"%conc]["btc"]["rx"]["rate_KBps"]["sum"] = sum(values)

        # Aggregate CPU RX
        values = [ data_aux["conn_%d"%c]["cpu"]["rx"]["avg"] for c in range(1, conc+1) ]
        data[d]["c=%d"%conc]["cpu"]["rx"] = calc(values)

        # Aggregate CPU TX
        values = [ data_aux["conn_%d"%c]["cpu"]["tx"]["avg"] for c in range(1, conc+1) ]
        data[d]["c=%d"%conc]["cpu"]["tx"] = calc(values)

#        btc_samples = {}
#        if len(conn_data) > 1:
#            temp = {}
#            temp["btc"] = {}
#            for c in range(1, conc+1):
#                temp["btc"]["conn_%d"%c] = {}
#                temp["btc"]["conn_%d"%c]["rx"] = {}
#                temp["btc"]["conn_%d"%c]["tx"] = {}
#
#                values = get_one_value_many_measurements(conn_data, "btc.conn_%d.rx.rate_KBps"%c)
#                temp["btc"]["conn_%d"%c]["rx"]["rate_KBps"] = str(calc(values, fun_toFloat)["avg"])
#                btc_samples[c] = [ fun_KBtoMB(float(x)) for x in values ]
#                
#                values = get_one_value_many_measurements(conn_data, "btc.conn_%d.rx.cpu"%c)
#                temp["btc"]["conn_%d"%c]["rx"]["cpu"] = str(calc(values, fun_perc)["avg"])
#                
#                values = get_one_value_many_measurements(conn_data, "btc.conn_%d.tx.cpu"%c)
#                temp["btc"]["conn_%d"%c]["tx"]["cpu"] = str(calc(values, fun_perc)["avg"])
#
#            conn_data = {"fake": temp}
#
#    
#        assert(len(conn_data) == 1)
#        measurement_name = list(conn_data.keys())[0] 
#        conn_data = conn_data[measurement_name]
#
#        values = get_many_values_one_measurement(conn_data, generate_keys("btc.conn_%d.rx.rate_KBps", conc))
#        data[d]["c=%d"%conc]["rx.rate_MBps"] = calc(values, fun_toFloat, fun_KBtoMB)
#        data[d]["c=%d"%conc]["rx.rate_MBps"]["per_connection"] = [ fun_KBtoMB(float(x)) for x in values ]
#        if len(btc_samples) > 0:
#            data[d]["c=%d"%conc]["rx.rate_MBps"]["samples"] = btc_samples
#
#        values = get_many_values_one_measurement(conn_data, generate_keys("btc.conn_%d.rx.cpu", conc))
#        data[d]["c=%d"%conc]["rx.cpu"] = calc(values, fun_perc)
#        del data[d]["c=%d"%conc]["rx.cpu"]["sum"]
#
#        values = get_many_values_one_measurement(conn_data, generate_keys("btc.conn_%d.tx.cpu", conc))
#        data[d]["c=%d"%conc]["tx.cpu"] = calc(values, fun_perc)
#        del data[d]["c=%d"%conc]["tx.cpu"]["sum"]

    del data[d]["raw"]
    json.dump(data, open("data.json", "w"), sort_keys=True, indent=4, separators=(',', ': '))

