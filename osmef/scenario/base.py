import time

import osmef.nuttcp
from osmef.scenario import BTC_SENDER, BTC_RECEIVER


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

        if config["type"] == BTC_RECEIVER:
            self.runner_type = BTC_RECEIVER
            self.receivers = []
            for count in range(config["incoming_count"]):
                self.receivers.append((osmef.nuttcp.CMD_PORT + count * 10, None))
        elif config["type"] == BTC_SENDER:
            self.peers = []
            tmp = {}
            for peer in config["receivers"]:
                peer = peer.strip()
                if peer in tmp:
                    tmp[peer] += 1
                else:
                    tmp[peer] = 0
                self.peers.append((None, peer, osmef.nuttcp.CMD_PORT + tmp[peer] * 10))
            self.duration = config["duration"]  # seconds

    def init(self, proto):
        proto.nuttcp_killall()
        if self.runner_type == BTC_RECEIVER:
            proto.nuttcp_spawn_servers(self.receivers)

    def run(self, proto):
        if self.runner_type == BTC_SENDER:
            self._prefill_results(proto)
            proto.nuttcp_measure(self.peers, self.duration)

    def get_result(self, proto):
        '''Called just after the run method to get the fresh results asynchronously.'''
        if self.runner_type == BTC_SENDER:
            self.result["btc"] = proto.nuttcp_results()
            return self.result
        else:
            return None

    def end(self, proto):
        proto.nuttcp_killall()


class NetBTCLocalhostScenario(BaseScenario):
    def __init__(self, config):
        super().__init__(config)
        self.receivers = []
        for count in range(config["concurrency"]):
            self.receivers.append((osmef.nuttcp.CMD_PORT + count * 10, None))

        self.peers = []
        counter = 0
        for peer in ["127.0.0.1"] * config["concurrency"]:
            self.peers.append((None, peer, osmef.nuttcp.CMD_PORT + counter * 10))
            counter += 1

        self.duration = config["duration"]  # seconds

        self.result["type"] = "Localhost BTC"
        self.result["concurrent"] = config["concurrency"]

    def init(self, proto):
        proto.nuttcp_killall()
        proto.nuttcp_spawn_servers(self.receivers)

    def run(self, proto):
        self._prefill_results(proto)
        proto.nuttcp_measure(self.peers, self.duration)

    def get_result(self, proto):
        '''Called just after the run method to get the fresh results asynchronously.'''
        self.result["btc"] = proto.nuttcp_results()
        return self.result

    def end(self, proto):
        proto.nuttcp_killall()
