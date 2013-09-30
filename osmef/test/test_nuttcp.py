import unittest

import osmef.nuttcp as nuttcp

sample_data = """nuttcp-t: v6.1.2: socket
nuttcp-t: buflen=65536 nstream=1 port=5001 mode=tcp host=127.0.0.1
nuttcp-t: time_limit=1.00
nuttcp-t: connect=127.0.0.1 mss=16384 rtt_ms=0.325
nuttcp-t: send_window_size=173400 receive_window_size=87380
nuttcp-t: send_window_avail=86700 receive_window_avail=43690
nuttcp-t: megabytes=1352.8125 real_seconds=1.00 rate_KBps=1385188.58 rate_Mbps=11347.4648
nuttcp-t: retrans=0
nuttcp-t: io_calls=21645 msec_per_call=0.05 calls_per_sec=21643.57
nuttcp-t: stats=cpu user=0.0 system=0.9 elapsed=0:01 cpu=92% memory=0i+0d-780maxrss io=0+3pf swaps=31+2207csw

nuttcp-r: v6.1.2: socket
nuttcp-r: buflen=65536 nstream=1 port=5001 mode=tcp
nuttcp-r: accept=127.0.0.1
nuttcp-r: send_window_size=173400 receive_window_size=87380
nuttcp-r: send_window_avail=86700 receive_window_avail=43690
nuttcp-r: megabytes=1352.8125 real_seconds=1.04 rate_KBps=1334233.56 rate_Mbps=10930.0413
nuttcp-r: megabytes=1352.8125 cpu_seconds=0.69 KB_per_cpu_second=2013365.46
nuttcp-r: io_calls=22852 msec_per_call=0.05 calls_per_sec=22009.92
nuttcp-r: stats=cpu user=0.0 system=0.6 elapsed=0:01 cpu=66% memory=0i+0d-306maxrss io=0+18pf swaps=21210+49csw
"""


class NutTcpTest(unittest.TestCase):
    def test_parse_output(self):
        ret = nuttcp._parse_output(sample_data)
        self.assertEqual(len(ret), 2)

