from configparser import ConfigParser
import logging
import os
import osmef.openstack
import osmef.ssh
import osmef.command_proto
log = logging.getLogger(__name__)


class ScenarioManager:
    def __init__(self):
        self.scenarios_avail = {}
        openstack_conffile = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "openstack.conf"))
        self.scenario_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "conf"))
        self.default_cfg_file = os.path.join(self.scenario_dir, "defaults.cfg")
        self._scan()
        self.active = None
        self.vm_setup = []
        self.openstack = osmef.openstack.OpenStack(openstack_conffile)

    def _scan(self):
        for f in os.listdir(self.scenario_dir):
            if f[-5:] != ".scen":
                continue
            self._load_one(f)

    def _load_one(self, scen_file):
        scen = ConfigParser()
        scen.read_file(open(self.default_cfg_file))
        scen.read(os.path.join(self.scenario_dir, scen_file))
        name = scen.get("description", "name")
        if name is None:
            log.warning("Invalid scenario: %s" % scen_file)
            return
        self.scenarios_avail[name] = scen

    def list_available(self):
        return self.scenarios_avail.keys()

    def select(self, scenario):
        if self.active is not None:
            raise RuntimeError("A scenario is already active")

        self.active = self.scenarios_avail[scenario]
        log.info("Selected scenario '%s'" % scenario)

        num_vms = int(self.active.get("description", "num_vms"))
        for i in range(1, num_vms + 1):
            vm = {}
            vm["name"] = "vm%d" % i
            vm["flavor"] = self.active.get("vm", "flavor")
            vm["image"] = self.active.get("vm", "image")
            vm["key"] = self.active.get("vm", "key")
            vm["keyfile"] = self.active.get("vm", "keyfile")
            vm["username"] = self.active.get("vm", "username")
            vm["zone"] = self.active.get("vm%d" % i, "zone")
            vm["num_mappers"] = int(self.active.get("vm%d" % i, "num_mappers"))
            vm["num_reducers"] = int(self.active.get("vm%d" % i, "num_reducers"))
            self.vm_setup.append(vm)

        self.openstack.spawn_vms(self.vm_setup)
        osmef.ssh.wait_boot(self.vm_setup)
        osmef.ssh.put_workers(self.vm_setup)
        osmef.ssh.start_workers(self.vm_setup)

        osmef.command_proto.init(self.vm_setup)

    def cleanup(self):
        if self.active is None:
            return

        osmef.command_proto.end(self.vm_setup)
        self.openstack.terminate_vms(self.vm_setup)
        self.active = None

