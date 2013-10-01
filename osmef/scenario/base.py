# These are not meant to be instantiated, ever.
# They must be subclassed
import osmef.nuttcp


class BaseScenario:
    def __init__(self, config):
        pass

    def init(self, proto):
        pass

    def run(self, proto):
        pass

    def end(self, proto):
        pass


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
        return proto.nuttcp_measure(self.peers, self.duration)

    def end(self, proto):
        proto.nuttcp_killall()


class NetBTCLocalhostScenario(NetBTCScenario):
    def __init__(self, config):
        self.concurrency = config["concurrency"]
        config["peers"] = ["127.0.0.1"] * self.concurrency
        config["peers"] = ",".join(config["peers"])
        config["receivers"] = self.concurrency
        super().__init__(config)

