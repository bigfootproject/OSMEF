import re

import osmef.ssh as ssh


def get_status(ip, use_namespace):
    ret = {}
    if use_namespace:
        conn = ssh.SshConnection("127.0.0.1")
    else:
        conn = ssh.SshConnection(ip)
    conn.connect()
    ret = _load(conn, ret)
    ret = _mem(conn, ret)
    ret = _bw(conn, ret)
    ret = _versions(conn, ret)
    return ret


def _versions(conn, out):
    # Linux bigfoot-m2 3.2.0-48-generic #74-Ubuntu SMP Thu Jun 6 19:43:26 UTC 2013 x86_64 x86_64 x86_64 GNU/Linux
    s = conn.run(["uname", "-a"])
    s = s.split(" ")
    out["kernel_version"] = s[2]
    return out


def _load(conn, out):
    # 2.60 2.15 2.03 5/406 32566
    s = conn.run(["cat", "/proc/loadavg"])
    s = s.split(" ")
    out["load_1"] = s[0]
    out["load_5"] = s[1]
    out["load_15"] = s[2]
    out["processes"] = s[3]
    return out


def _mem(conn, out):
    s = conn.run(["cat", "/proc/meminfo"])
    m = re.search("MemTotal:\s+(\d+) kB", s)
    out["mem_total"] = m.group(1)
    m = re.search("MemFree:\s+(\d+) kB", s)
    out["mem_free"] = m.group(1)
    m = re.search("Buffers:\s+(\d+) kB", s)
    out["buffers"] = m.group(1)
    m = re.search("Cached:\s+(\d+) kB", s)
    out["cached"] = m.group(1)
    m = re.search("SwapTotal:\s+(\d+) kB", s)
    out["swap_total"] = m.group(1)
    m = re.search("SwapFree:\s+(\d+) kB", s)
    out["swap_free"] = m.group(1)
    m = re.search("Slab:\s+(\d+) kB", s)
    out["slab_total"] = m.group(1)
    m = re.search("SReclaimable:\s+(\d+) kB", s)
    out["slab_reclaimable"] = m.group(1)
    m = re.search("SUnreclaim:\s+(\d+) kB", s)
    out["slab_unreclaimed"] = m.group(1)
    return out


def _bw(conn, out):
    # unix timestamp[0];iface_name[1];bytes_out/s[2];bytes_in/s[3];bytes_total/s[4];bytes_in[5];bytes_out[6];packets_out/s[7];packets_in/s[8];packets_total/s[9];packets_in[10];packets_out[11];errors_out/s[12];errors_in/s[13];errors_in[14];errors_out[15]
    s = conn.run(["bwm-ng", "-o", "csv", "-c", "1", "-T", "rate", "-t", "5000"])
    s = s.split("\n")
    for l in s:
        l = l.split(";")
        if len(l) < 2:
            continue
        tmp = {}
        tmp["bytes_outS"] = l[2]
        tmp["bytes_inS"] = l[3]
        tmp["packets_outS"] = l[7]
        tmp["packets_inS"] = l[8]
        tmp["errors_outS"] = l[12]
        tmp["errors_inS"] = l[13]
        out["net_"+l[1]] = tmp
    return out

