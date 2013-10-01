import unittest

import osmef.command_protocol as osmef_cp


class FakeSocket:
    def __init__(self):
        self.stuff_sent = ""
        self.stuff_received = ""

    def send(self, stuff):
        self.stuff_sent += stuff

    def recv(self, count, flags):
        ret = self.stuff_received[:count]
        self.stuff_received = self.stuff_received[count:]
        return ret


class CommandProtocolTest(unittest.TestCase):
    def test_send_object(self):
        obj = {"test": 1}
        s = FakeSocket()
        osmef_cp._send_object(s, obj)
        assert s.stuff_sent == '0000000011{"test": 1}'

    def test_receive_object(self):
        s = FakeSocket()
        s.stuff_received = '0000000011{"test": 1}'
        obj = osmef_cp._receive_object(s)
        assert obj == {"test": 1}

