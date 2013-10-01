#!/usr/bin/python

import re
import threading
import queue
import traceback
from subprocess import check_output, call, CalledProcessError
import logging
log = logging.getLogger(__name__)

TRANSFER_DURATION = "1"  # use 5m for 5 minutes, see nuttcp transfer timeout syntax
CMD_PORT = 7100
NUTTCP_EXECUTABLE = "nuttcp"


def killall():
    """Kill all instances
    of nuttcp running on this host.
    Needed to cleanup before and after a run."""
    call(["killall", "nuttcp"])


def run_server(port, namespace):
    """Run a nuttcp receiver. Can be called as many times as needed, with a different ports. Will return immediately."""
    cmd = [NUTTCP_EXECUTABLE, "-S", "-P%d" % (port), "-p%d" % (port + 1,)]
    if namespace:
        cmd = ["ip", "netns", "exec", namespace] + cmd
    call(cmd)


def run_client(server_ip, server_port, duration, namespace):
    """Run a nuttcp transmitter. Will wait till the end of the run and then return the parsed output."""
    cmd = [NUTTCP_EXECUTABLE, "-P%d" % server_port, "-p%d" % (server_port + 1,), "-T%s" % duration, "-v", "-fparse", server_ip]
    if namespace:
        cmd = ["ip", "netns", "exec", namespace] + cmd
    retry = 0
    while retry < 5:
        try:
            out = check_output(cmd)
            break
        except CalledProcessError:
            print("--------> EXCEPTION running %s <--------" % str(cmd))
            traceback.print_exc()
            print("----------------------------------------")
            retry += 1
            if retry < 5:
                log.warning("---> Retrying after exception.")
    if retry >= 5:
        log.error("Connection error for 5 consecutive times")
        out = None

    return _parse_output(out)


def _parse_output(output):
    if output is None:
        return {"res", "error"}
    output = output.decode("ascii")
    res = {"tx": {}, "rx": {}}
    output = output.split("\n")
    if len(output[-1]) < 10:
        output = output[:-1]
    acc = []
    for l in output:
        if len(l) < 10:
            tx_out = acc
            acc = []
            continue
        acc.append(l)
    rx_out = acc
    rx_out = "\n".join(rx_out)
    tx_out = "\n".join(tx_out)

    for m in re.finditer("\w+=\S+", rx_out):
        (key, value) = m.group(0).split("=")
        res["rx"][key] = value
    for m in re.finditer("\w+=\S+", tx_out):
        (key, value) = m.group(0).split("=")
        res["tx"][key] = value

    return res


def run_client_thread(server_ip, server_port, duration, q, namespace):
    def aux(server_ip, server_port, duration, namespace, q):
        ret = run_client(server_ip, server_port, duration, namespace)
        q.put(ret)

    th = threading.Thread(target=aux, args=(server_ip, server_port, duration, namespace, q))
    th.start()
    return th


def spawn_servers(ns_ports):
    for port, ns in ns_ports:
        log.debug("Spawning nuttcp receiver on ns {0} and port {1}".format(ns, port))
        run_server(port, ns)


def measure(servers, duration):
    q = queue.Queue()
    clients = []
    counter = 0
    for ns, srv_ip, srv_port in servers:
        counter += 1
        log.info("Spawning transmitter nr. %d that connects to %s:%d" % (counter, srv_ip, srv_port))
        th = run_client_thread(srv_ip, srv_port, duration, q, ns)
        clients.append(th)
    results = {}
    counter = 1
    for th in clients:
        th.join()
        results["conn_%d" % counter] = q.get()
        counter += 1
    return results


def measure_btc_generic(server_ips, ssh_client_ips, server_listen_ips, duration, use_namespace):
    """Nuttcp has an inefficient server mode, for this reason we will run a
    server instance for each client, on a different port."""
    if len(server_ips) != len(ssh_client_ips) or len(server_listen_ips) != len(ssh_client_ips):
        print("Error: wrong number of arguments: server_ips(%d), ssh_client_ips(%d), server_listen_ips(%d)" % (len(server_ips), len(ssh_client_ips), len(server_listen_ips)))
        return None

    if use_namespace:
        killall("127.0.0.1")
    else:
        ips = set(server_ips)  # remove duplicates
        for ip in ips:
            killall(ip)
    servers = []
    port = CMD_PORT
    for idx in range(len(server_ips)):
        print("Running receiver on %s:%d" % (server_ips[idx], port))
        servers.append((run_server(server_ips[idx], port, use_namespace), port))  # servers listen on all available interfaces
        port += 10
    q = queue.Queue()
    clients = []
    for idx in range(len(servers)):
        host = ssh_client_ips[idx]
        server_port = servers[idx][1]
        server_ip = server_listen_ips[idx]
        print("Spawning transmitter nr. %d on %s that connects to %s" % (idx + 1, ssh_client_ips[idx], server_listen_ips[idx]))
        th = run_client_thread(host, server_ip, server_port, duration, q, use_namespace)
        clients.append(th)
    results = {}
    counter = 1
    for th in clients:
        th.join()
        results["conn_%d" % counter] = q.get()
        counter += 1

    if use_namespace:
        killall("127.0.0.1")
    else:
        ips = set(server_ips)  # remove duplicates
        for ip in ips:
            killall(ip)

    return results


def measure_btc_localhost(host, concurrency, duration):
    results = measure_btc_generic([host] * concurrency, [host] * concurrency, ["127.0.0.1"] * concurrency, duration, False)
    return results


def measure_btc(receiver, transmitters, duration, use_namespace):
    if "@" in receiver:
        listen_ip = receiver.split("@")[1]
    else:
        listen_ip = receiver
    results = measure_btc_generic([receiver] * len(transmitters), transmitters, [listen_ip] * len(transmitters), duration, use_namespace)
    return results

