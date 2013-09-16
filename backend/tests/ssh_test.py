import unittest

import ssh

class SshTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        ret = ssh.SshConnection("127.0.0.1")
        self.assertIsNotNone(ret)

    def test_connect_local(self):
        ret = ssh.SshConnection("127.0.0.1")
        ret.connect()
        self.assertIsNotNone(ret.conn)

    def test_connect_remote(self):
        ret = ssh.SshConnection("192.168.46.10")
        ret.connect()
        self.assertIsNotNone(ret.conn)

    def test_run(self):
        ret = ssh.SshConnection("127.0.0.1")
        ret.connect()
        output = ret.run(["echo", "test"])
        self.assertEqual(output.strip(), "test")


