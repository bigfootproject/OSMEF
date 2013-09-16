import unittest

from osmef.config import conf_store

class ConfigTests(unittest.TestCase):
    def test_getopt(self):
        self.assertIsNone(conf_store._getopt("nosection", "noname"))
        self.assertIsNotNone(conf_store._getopt("ssh", "private_key"))

