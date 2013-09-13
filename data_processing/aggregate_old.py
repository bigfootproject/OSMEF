#!/usr/bin/python

import sys, os, re
import json
import argparse
import pprint

arg_parser = argparse.ArgumentParser(description='Define tests')
arg_parser.add_argument('-p', '--pretty-print', action="store_true", help="select human friendly output, default is CSV")
arg_parser.add_argument('-i', '--info', action="store_true", help="show info about the data available in the specified directory")
arg_parser.add_argument('-k', '--show-keys', action="store_true", help="show available keys")
arg_parser.add_argument('-a', '--all-connections', action="store_true", help="extract results for all connections")
arg_parser.add_argument('-c', '--concurrent', default=0, help="filter results with specified concurrency", type=int)
arg_parser.add_argument('in_dir', help="Input directory contatining JSON files")
arg_parser.add_argument('keys', nargs=argparse.REMAINDER, help="keys to extract")

args = arg_parser.parse_args()

def load_json(fname):
    return json.load(open(fname, "r"))

def load_all(src_dir):
    data = {}
    file_list = os.listdir(src_dir)
    for f in file_list:
        if not os.path.splitext(f)[1] == ".json":
            continue
        fp = os.path.join(src_dir, f)
        try:
            data[f] = load_json(fp)
        except ValueError:
            print("Skipping corrupted file: %s" % f)
            continue
    return data

def dotkey(tree_root, dotted_key):
    dotted_key = dotted_key.split(".")
    value = tree_root
    for key in dotted_key:
        value = value[key]
    return value

def get_keys(f):
    keys = []
    t = data[f]
    unvisited = list(t.keys())
    while len(unvisited) > 0:
        k = unvisited.pop()
        child = dotkey(t, k)
        if type(child) != dict:
            keys.append(k)
        else:
            for kname in child.keys():
                unvisited.append(k+"."+kname)
    return keys
#        unvisited += t[k]
#    values = []
#    k = key.split(".")
#    for d in data:
#        values.append(get_value(d, k))
#    return values

def print_csv_header(columns):
    out = "measurement"
    for title in columns:
        out += ", " + title
    print(out)

def get_values_measurement(tree, keys):
    out = []
    for key in keys:
        try:
            out.append(dotkey(tree, key))
        except KeyError:
            out.append("N/A")
    return out

def print_values(measure, values):
    if args.pretty_print:
        print("Measure: %s" % measure)
        for v in values:
            print("\t%s" % (v,))
    else:
        s = measure
        for v in values:
            s += "," + str(v)
        print(s)

def expand_keys(template_measure):
    """For each key that contains conn_N will add all other conn_* keys with the
    same suffix"""
    new_keys = args.keys[:]
    all_keys = get_keys(template_measure)
    for ukey in args.keys:
        match = re.search(r"conn_[0-9]+\.", ukey)
        if match:
            suffix = ukey[match.end():]
            new_keys.remove(ukey)
            for skey in all_keys:
                if re.search(suffix+"$", skey):
                    new_keys.append(skey)
    return new_keys

def filter_measures(data, concurrent):
    """Return a filtered data dictionary containing only the selected concurrent number"""
    measures = list(data.keys())
    for measure in measures:
        conc = get_values_measurement(data[measure], ["concurrent"])[0]
        if conc != concurrent:
            del data[measure]
    return data

data = load_all(args.in_dir)

if args.info:
    descrs = get_all_values("name")
    print("These measurements are available:")
    for d in sorted(descrs, key=lambda x: int(x.split("_")[0])):
        print(d, ":", descrs[d][0])
    sys.exit(0)

if args.show_keys:
    f = sorted(data.keys())[-1]
    print("Reading keys from file %s" % f)
    ks = get_keys(f)
    for k in sorted(ks):
        print(k)
    sys.exit(0)

if args.all_connections and args.concurrent == 0:
    print("Error: -a requires -c")
    sys.exit(1)

if args.concurrent != 0:
    data = filter_measures(data, args.concurrent)

if args.all_connections:
    new_keys = expand_keys(list(data.keys())[0])
else:
    new_keys = args.keys[:]

if not args.pretty_print:
    print_csv_header(new_keys)

for measure in data.keys():

    values = get_values_measurement(data[measure], new_keys)
    print_values(measure, values)

