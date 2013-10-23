import os
from subprocess import call
import logging

from osmef.command_protocol import OSMeFRunner

log = logging.getLogger(__name__)

# Runner types
HOST_RUNNER = 1

# Measurement roles
BTC_SENDER = 1
BTC_RECEIVER = 2


class BaseRunner:
    def __init__(self, name, runner_type, measurement_type):
        self.name = name
        self.runner_type = runner_type
        self.measurement_class = measurement_type
        self.measurement = None
        self.config = {}
        self.proto = None

    def set_config(self, config):
        required_settings = ["ip", "ssh_user", "ssh_key", "role"]
        for s in required_settings:
            if s not in config:
                log.error("Missing required config entry '%s'" % s)
                raise ValueError
        self.config = config
        self.measurement = self.measurement_class(self.config)

    def spawn(self):
        osmef_dir = os.path.basename(os.path.abspath(__file__))
        osmef_dir = os.path.abspath(os.path.join(osmef_dir, ".."))
        cmd = ["ssh", "-i", self.config["ssh_key"], "{0}@{1}".format(self.config["ssh_user"], self.config["ip"]), "mkdir", "-f", "/tmp/osmef"]
        call(cmd)
        log.debug("Copying OSMeF files to %s" % self.config["ip"])
        cmd = ["scp", "-r", "-i", self.config["ssh_key"], osmef_dir + "/*", "{0}@{1}:/tmp/osmef".format(self.config["ssh_user"], self.config["ip"])]
        call(cmd)
        log.debug("Remotely executing runner %s" % self.name)
        cmd = ["ssh", "-i", self.config["ssh_key"], "{0}@{1}".format(self.config["ssh_user"], self.config["ip"]), "/tmp/osmef/bin/runner.py"]
        call(cmd)

    def connect(self):
        log.debug("Connecting to runner %s" % self.name)
        self.proto = OSMeFRunner(self.config["ip"])

    def scenario_init(self):
        self.measurement.init(self.proto)

    def scenario_run(self):
        self.measurement.run()

    def scenario_get_results(self):
        return self.measurement.get_results()

    def scenario_end(self):
        self.measurement.quit()


class HostRunner(BaseRunner):
    def __init__(self, name, measurement_type):
        super().__init__(name, HOST_RUNNER, measurement_type)

