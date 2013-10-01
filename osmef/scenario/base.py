import time

import osmef.nuttcp


class BaseScenario:
    def __init__(self, config):
        self.result = {}

    def init(self, proto):
        raise NotImplementedError

    def run(self, proto):
        raise NotImplementedError

    def get_result(self, proto):
        raise NotImplementedError

    def end(self, proto):
        raise NotImplementedError

    def _prefill_results(self, proto):
        '''Called by the run method just before the measurement'''
        self.result["state_sender"] = proto.gather_status()
        self.result["time"] = time.time()


class NetBTCScenario(BaseScenario):
    def __init__(self, config):
        super().__init__(config)
        self.peers = []
        tmp = {}
        for peer in config["peers"].split(","):
            peer = peer.strip()
            if peer in tmp:
                tmp[peer] += 1
            else:
                tmp[peer] = 0
            self.peers.append((None, peer, osmef.nuttcp.CMD_PORT + tmp[peer] * 10))
        self.duration = config["duration"]  # seconds
        self.receivers = []
        for count in range(config["receivers"]):
            self.receivers.append((osmef.nuttcp.CMD_PORT + count * 10, None))

    def init(self, proto):
        proto.nuttcp_killall()
        proto.nuttcp_spawn_servers(self.receivers)

    def run(self, proto):
        self._prefill_results(proto)
        proto.nuttcp_measure(self.peers, self.duration)

    def get_result(self, proto):
        '''Called just after the run method to ghe the fresh results asynchronously.'''
        self.result["btc"] = proto.nuttcp_results()
        return self.result

    def end(self, proto):
        proto.nuttcp_killall()


class NetBTCLocalhostScenario(NetBTCScenario):
    def __init__(self, config):
        self.concurrency = config["concurrency"]
        config["peers"] = ["127.0.0.1"] * self.concurrency
        config["peers"] = ",".join(config["peers"])
        config["receivers"] = self.concurrency
        super().__init__(config)

        self.result["type"] = "Localhost BTC"
        self.result["concurrent"] = self.concurrency
