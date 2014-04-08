import socket
import struct

CMD_LISTEN_PORT = 2333

MSG_FMT = "!I1024s"
CMD_EXIT = 0
CMD_INIT = 1
CMD_NODES = 2


def _connect_worker(vm):
    vm["conn"] = socket.create_connection((vm["ip"], 2333))


def _send_msg(s, cmd, data):
    msg = struct.pack(MSG_FMT, cmd, bytes(data, "ASCII"))
    s.send(msg)


def init(vm_setup):
    for vm in vm_setup:
        _connect_worker(vm)
        _send_msg(vm["conn"], CMD_INIT, "")
        _send_msg(vm["conn"], CMD_NODES, str(vm["num_reducers"] + vm["num_mappers"]))


def end(vm_setup):
    for vm in vm_setup:
        _send_msg(vm["conn"], CMD_EXIT, "")
