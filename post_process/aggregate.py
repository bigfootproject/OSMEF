#!/usr/bin/python

import sys
import os
import json
import numpy
from pprint import pprint


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


def load_all(src_dir, scenario):
    data = {}
    file_list = os.listdir(src_dir)
    for f in file_list:
        if not scenario + "-" in f:
            continue
        if not os.path.isdir(os.path.join(src_dir, f)):
            continue
        fp = os.path.join(src_dir, f, "summary.json")
        try:
            data[f] = load_json(fp)
        except ValueError:
            print("Skipping corrupted file: %s" % f)
            continue
    return data


def calc(values, fun_pre=lambda x: x, fun_after=lambda x: x):
    values = [fun_pre(x) for x in values]
    values = numpy.array(values)
    out = {}
    out["avg"] = fun_after(numpy.average(values))
#    out["sum"] = fun_after(numpy.sum(values))
    out["std"] = fun_after(numpy.std(values))
    out["count"] = len(values)
    return out


def calc_bw(sizes_bit, times_ns, fun_pre=lambda x: x):
    bw = []
    assert(len(sizes_bit) == len(times_ns))
    for i in range(len(sizes_bit)):
        t = fun_pre(times_ns[i])
        if t == 0:
            t = 0.001
        bw.append((fun_pre(sizes_bit[i]) * 8) / (t / 1000.0))
    out = {}
    out["avg"] = numpy.average(bw)
    out["std"] = numpy.std(bw)
    out["count"] = len(bw)
    return out


def generate_keys(key_template, count):
    out = []
    for idx in range(count):
        out.append(key_template % (idx + 1,))
    return out


def preprocess(data):
    for m in data:
        for vm in data[m]:
            aux = {}
            for node in data[m][vm]:
                tmp = {}
                count = 0
                for conn in data[m][vm][node]:
                    tmp["c%d" % count] = conn
                    count += 1
                node_n = node.split(":")[1]
                aux[node_n] = tmp
            data[m][vm] = aux


if len(sys.argv) < 3:
    print("Usage: ./aggregate.py <base_dir> <scenario_name>")
    sys.exit(1)

base_dir = sys.argv[1]
scenario = sys.argv[2]

data = {}
data[scenario] = {}
data[scenario]["raw"] = load_all(base_dir, scenario)
data[scenario]["aggr"] = NestedDict()

preprocess(data[scenario]["raw"])

fun_toInt = lambda x: int(x.strip())

throughput = 0
throughput_std = 0
first_sample = list(data[scenario]["raw"].keys())[0]
for vm in data[scenario]["raw"][first_sample]:
    print("Looking at VM %s for sample %s" % (vm, first_sample))
    for node in data[scenario]["raw"][first_sample][vm]:
        for conn in data[scenario]["raw"][first_sample][vm][node]:
            b = get_one_value_many_measurements(data[scenario]["raw"], "%s.%s.%s.bytes" % (vm, node, conn))
            data[scenario]["aggr"][vm][node][conn]["bytes"] = calc(b, fun_toInt)
            c = get_one_value_many_measurements(data[scenario]["raw"], "%s.%s.%s.cpu_time" % (vm, node, conn))
            data[scenario]["aggr"][vm][node][conn]["cpu_time"] = calc(c, fun_toInt)
            t = get_one_value_many_measurements(data[scenario]["raw"], "%s.%s.%s.time_elapsed" % (vm, node, conn))
            data[scenario]["aggr"][vm][node][conn]["time_elapsed"] = calc(t, fun_toInt)
#            bw = (data[scenario]["aggr"][vm][node][conn]["bytes"]["avg"] * 8) / (data[scenario]["aggr"][vm][node][conn]["time_elapsed"]["avg"] / 1000.0)
#            data[scenario]["aggr"][vm][node][conn]["bandwidth_bit_sec"] = bw
            data[scenario]["aggr"][vm][node][conn]["bandwidth_bit_sec"] = calc_bw(b, t, fun_toInt)
            if "r" in node:
                throughput += data[scenario]["aggr"][vm][node][conn]["bandwidth_bit_sec"]["avg"]
                throughput_std += data[scenario]["aggr"][vm][node][conn]["bandwidth_bit_sec"]["std"] ** 2

data[scenario]["aggr"]["total_throughput_bit_sec"]["thr"] = throughput
data[scenario]["aggr"]["total_throughput_bit_sec"]["std"] = numpy.sqrt(throughput_std)

print("Writing summary for scenario %s" % scenario)

json.dump(data, open("%s_summary.json" % scenario, "w"), sort_keys=True, indent=4, separators=(',', ': '))

