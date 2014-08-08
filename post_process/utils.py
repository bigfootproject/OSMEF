from configparser import ConfigParser
import os
import json

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCEN_PATH = os.path.join(BASE_PATH, "osmef/scenario/conf")
EXP_PATH = os.path.join(BASE_PATH, "experiments")

def load_experiments(scenario, experiment):
    paths = []
    data = []
    for dn in os.listdir(os.path.join(EXP_PATH, experiment)):
        d = os.path.join(EXP_PATH, experiment, dn)
        if not os.path.isdir(d):
            continue
        if scenario + "-" in d:
            paths.append((os.path.join(EXP_PATH, experiment, d), dn))
    for p in paths:
        data.append(json.load(open(os.path.join(p[0], "summary.json"))))
        data[-1]["scenario_name"] = p[1]
    return data

def scen_name(scen_name):
    scen = ConfigParser()
    scen.read_file(open(os.path.join(SCEN_PATH, scen_name + ".scen")))
    return scen.get("description", "name")

def scen_num_vms(scen_name):
    scen = ConfigParser()
    scen.read_file(open(os.path.join(SCEN_PATH, scen_name + ".scen")))
    return int(scen.get("description", "num_vms"))

def scen_shuffle_size(scen_name):
    scen = ConfigParser()
    scen.read_file(open(os.path.join(SCEN_PATH, scen_name + ".scen")))
    return int(scen.get("description", "total_shuffle_size")) * 1024 * 1024 * 1024

def scen_num_mappers(scen_name, vm):
    scen = ConfigParser()
    scen.read_file(open(os.path.join(SCEN_PATH, scen_name + ".scen")))
    return int(scen.get(vm, "num_mappers"))

def scen_num_reducers(scen_name, vm):
    scen = ConfigParser()
    scen.read_file(open(os.path.join(SCEN_PATH, scen_name + ".scen")))
    return int(scen.get(vm, "num_reducers"))

def conn_calc_bw(conn):
    return (int(conn['bytes']) * 8) / (int(conn["time_elapsed"]) / 1000)  # bit/s

def red_calc_bw(red):
    bw = 0
    for conn in red:
        bw += conn_calc_bw(conn)
    return bw

def vm_calc_bw(vm):
    bw = 0
    for node in vm:
        if ":m" in node:
            continue
        bw += red_calc_bw(vm[node])
    return bw

def exp_calc_bw(exp):
    bw = 0
    for vm in exp:
        bw += vm_calc_bw(exp[vm])
    return bw

