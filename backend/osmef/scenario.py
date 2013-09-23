import nuttcp


class BTCScenario:
    def __init__(self):
        self.peers = []
        self.duration = 10  # seconds
        self.concurrency = 1
        self.ssh_keyfile = None

    def run(self):
        peers = self.peers * self.concurrency
        return nuttcp.measure_btc_generic(peers, self.duration, self.ssh_keyfile)


class LocalhostBTCScenario:
    def __init__(self):
        self.host = None
        self.duration = 10
        self.concurrency = 1
        self.ssh_keyfile = None

    def run(self):
        return nuttcp.measure_btc_localhost(self.host, self.concurrency, self.duration)

