import socketserver
import socket
import json
import sys
import logging
log = logging.getLogger(__name__)

import osmef.nuttcp
import osmef.os_status

DEFAULT_PORT = 9544


class OSMeFProtoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        osmef_proto = OSMeFClient(self.request)
        # self.request is the TCP socket connected to the client
        req = osmef_proto.receive_object()
        while "quit" not in req:
            log.info("handling '{0}' call".format(req["call"]))
            try:
                callback = getattr(osmef_proto, req["call"])
            except AttributeError:
                log.error("Unknown request received: {0}".format(req["call"]))
                ret = None
            else:
                ret = callback(**req["args"])
            osmef_proto.send_object(ret)
            req = osmef_proto.receive_object()
        log.info("Connection closed")


class OSMeFProtocolBase:
    def __init__(self, sock):
        self.sock = sock

    def send_object(self, obj):
        log.debug("sending object")
        obj_s = json.dumps(obj).encode("utf-8")
        obj_len = "{0:0=-10d}".format(len(obj_s)).encode("utf-8")
        self.sock.send(obj_len)
        self.sock.send(obj_s)

    def receive_object(self):
        log.debug("receiving object")
        obj_len = self.sock.recv(10, socket.MSG_WAITALL)
        if len(obj_len) < 10:
            return {"quit": True}
        obj_len = int(obj_len.decode("utf-8"))
        obj_s = self.sock.recv(obj_len, socket.MSG_WAITALL).decode("utf-8")
        return json.loads(obj_s)


class OSMeFClient(OSMeFProtocolBase):
    '''For communication from a runner to the client'''
    def __init__(self, sock):
        super().__init__(sock)

    def exit(self):
        log.info("exit message, ending execution")
        sys.exit(0)

    def gather_status(self):
        return osmef.os_status.get_status()

    def nuttcp_killall(self, **kw):
        return osmef.nuttcp.killall()

    def nuttcp_spawn_servers(self, receivers):
        return osmef.nuttcp.spawn_servers(receivers)

    def nuttcp_measure(self, peers, duration):
        return osmef.nuttcp.measure(peers, duration)


class OSMeFRunner(OSMeFProtocolBase):
    ''' For communication from the client to a particular runner'''
    def __init__(self, ip):
        super().__init__(None)
        self.connect(ip)

    def exit(self):
        req = {}
        req["call"] = "exit"
        req["args"] = {}
        self.send_object(req)
        self.sock = None
        return

    def quit(self):
        req = {"quit": True}
        self.send_object(req)
        self.sock = None

    def connect(self, ip):
        log.info("Connecting to runner on {0}".format(ip))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect((ip, DEFAULT_PORT))
        except Exception as e:
            log.error("Cannot connect to runner instance on {0}".format(ip))
            log.error(str(e))
            self.sock = None

    def gather_status(self):
        req = {}
        req["call"] = "gather_status"
        req["args"] = {}
        self.send_object(req)
        return self.receive_object()

    def nuttcp_killall(self):
        req = {}
        req["call"] = "nuttcp_killall"
        req["args"] = {}
        self.send_object(req)
        return self.receive_object()

    def nuttcp_spawn_servers(self, receivers):
        req = {}
        req["call"] = "nuttcp_spawn_servers"
        req["args"] = {}
        req["args"]["receivers"] = receivers
        self.send_object(req)
        return self.receive_object()

    def nuttcp_measure(self, peers, duration):
        req = {}
        req["call"] = "nuttcp_measure"
        req["args"] = {}
        req["args"]["peers"] = peers
        req["args"]["duration"] = duration
        self.send_object(req)
        return None

    def nuttcp_results(self):
        return self.receive_object()

