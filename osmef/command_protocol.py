import socketserver
import socket
import json
import logging
log = logging.getLogger(__name__)

DEFAULT_PORT = 9544

_callbacks = {}


class OSMeFProtoHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # self.request is the TCP socket connected to the client
        req = _receive_object(self.request)
        log.info("handling {0} call".format(req["call"]))
        if req["call"] in _callbacks:
            ret = _callbacks[req["call"]](**req["args"])
        else:
            log.error("unknown request received: {0}".format(req["call"]))
        _send_object(self.request, ret)


def _send_object(s, obj):
    obj_s = json.dumps(obj)
    obj_len = "{0=-10d}".format(len(obj_s))
    s.send(obj_len)
    s.send(obj_s)


def _receive_object(s):
    obj_len = s.recv(10)
    obj_len = int(obj_len)
    obj_s = s.recv(obj_len, socket.MSG_WAITALL)
    return json.loads(obj_s)

