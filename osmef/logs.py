import json

# *RES* start node vm1:r0
# *RES* vm1:r0:1,1397726448491,342,44,153391690
# *RES* vm1:r0:2,1397726448491,366,48,153391690
# *RES* vm1:r0:0,1397726448492,434,57,153391690
# *RES* vm1:r0:4,1397726448491,3976,657,153391690
# *RES* vm1:r0:3,1397726448491,5317,706,153391690
# *RES* vm1:r0:2,1397726448935,4945,741,153391690
# *RES* vm1:r0:1,1397726448935,5119,743,153391690
# *RES* end node vm1:r0


def is_result_line(line):
    return "*RES* " == line[:6]


def parse_one_log(log):
    ret = {}
    node = []
    node_name = ""
    log = [l.strip() for l in log.split("\n")]
    for l in log:
        if not is_result_line(l):
            continue
        l = l[6:]
        if "start node" in l:
            node = []
            node_name = l.split()[2]
            continue
        if "end node" in l:
            ret[node_name] = node
            continue
        l = l.split(",")
        meas = {}
        meas["name"] = l[0]
        meas["peer_name"] = l[1]
        meas["wall_time_start"] = l[2]
        meas["time_elapsed"] = l[3]
        meas["cpu_time"] = l[4]
        meas["bytes"] = l[5]
        node.append(meas)
    return ret


def parse(logs):
    res = {}
    for k in logs:
        res[k] = parse_one_log(logs[k])
    return json.dumps(res)
