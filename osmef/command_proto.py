import logging
log = logging.getLogger(__name__)
import socket
import struct

CMD_LISTEN_PORT = 2333

commands = {
    'CMD_EXIT': 0,
    'CMD_INIT': 1,
    'CMD_NODES': 2,
    'CMD_MAPPER': 3,
    'CMD_REDUCER': 4,
    'CMD_START': 5
}


def _connect_worker(vm):
    vm["conn"] = socket.create_connection((vm["ip"], 2333))


def _send_msg(vm, cmd, data):
    if not "conn" in vm:
        log.error("Cannot send command: no connection")
        return
    log.debug("Sending command {} to '{}'".format(cmd, vm["name"]))
    msg = "{}|{}".format(commands[cmd], data)
    print(msg)
    if len(msg) > 1024:
        log.error("Sending message longer than 1024 bytes, it will be truncated")
    msg = struct.pack("1024s", bytes(msg, "ASCII"))
    vm["conn"].send(msg)


def _recv_reply(vm):
    data = vm["conn"].recv(1024)
    try:
        data = struct.unpack("1024s", data)[0]
    except struct.error:
        return None
    data = bytearray(data)
    term = data.index(bytes('\x00', "ASCII"))
    data = data[0:term].decode("ASCII")
    return data


def _recv_done(vm):
    rep = _recv_reply(vm)
    if rep == "DONE":
        return True
    else:
        log.error("Expecting DONE, got {}".format(rep))
        return False


def init(vm_setup):
    for vm in vm_setup:
        _connect_worker(vm)
        _send_msg(vm, "CMD_INIT", "")
        _send_msg(vm, "CMD_NODES", "{},{}".format(vm["num_mappers"], vm["num_reducers"]))
        ret = _recv_done(vm)
        if not ret:
            return False
        for m in vm["mappers"]:
            msg = m.to_str()
            _send_msg(vm, "CMD_MAPPER", msg)
            ret = _recv_done(vm)
            if not ret:
                return False
        for r in vm["reducers"]:
            msg = r.to_str()
            _send_msg(vm, "CMD_REDUCER", msg)
    return True


def start_measurement(vm_setup):
    for vm in vm_setup:
        _send_msg(vm, "CMD_START", "")
    for vm in vm_setup:
        ret = _recv_done(vm)
        if not ret:
            return False
    return True


def end(vm_setup):
    for vm in vm_setup:
        _send_msg(vm, "CMD_EXIT", "")
