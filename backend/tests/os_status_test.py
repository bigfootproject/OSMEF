import unittest

import os_status

class OsStatusTest(unittest.TestCase):
    def get_status_test(self):
        ret = os_status.get_status("127.0.0.1", False)
        self.assertIsNotNone(ret)
        self.assertNotEqual(len(ret), 0)

