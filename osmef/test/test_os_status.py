import unittest

import osmef.os_status as os_status


class OsStatusTest(unittest.TestCase):
    def test_get_status_test(self):
        ret = os_status.get_status()
        self.assertIsNotNone(ret)
        self.assertNotEqual(len(ret), 0)
