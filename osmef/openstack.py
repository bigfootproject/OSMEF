import openstack_api
import openstack_api.compute
import configparser
import logging
log = logging.getLogger(__name__)
import time


class OpenStack:
    def __init__(self, conffile):
        self.conf = configparser.ConfigParser()
        self.conf.read_file(open(conffile))

    def spawn_vms(self, vm_setup):
        creds = openstack_api.get_creds(self.conf)
        for vm in vm_setup:
            ret = openstack_api.compute.find_instance(creds, vm["name"])
            if ret is None:
                log.info("Spawning new VM '%s'" % vm["name"])
                ret = openstack_api.compute.create_server(creds, vm["name"], vm["flavor"], vm["image"], vm["zone"], vm["key"])
            else:
                log.info("Reusing existing VM '%s'" % vm["name"])
            vm["instance"] = ret
        while True:
            wait = False
            for vm in vm_setup:
                if vm["instance"].status == 'BUILD':
                    vm["instance"] = openstack_api.compute.refresh_instance(creds, vm["instance"])
                    log.debug("VM '%s' not yet ready" % vm["name"])
                    wait = True
                elif "ip" not in vm:
                    vm["private_ip"] = openstack_api.compute.get_private_ip(creds, vm["instance"])
                    vm["ip"] = openstack_api.compute.get_floating_ip(creds, vm["instance"])
                    if len(vm["private_ip"]) == 1:
                        vm["private_ip"] = vm["private_ip"][0]
                    elif vm["ip"] in vm["private_ip"]:
                        vm["private_ip"] = [ip for ip in vm["private_ip"] if ip != vm["ip"]][0]
                    log.debug("VM '%s' is READY, private IP is %s, floating IP is %s" % (vm['name'], vm["private_ip"], vm["ip"]))
            if wait:
                time.sleep(5)
            else:
                log.info("All VMs in status READY")
                break

    def terminate_vms(self, vm_setup):
        creds = openstack_api.get_creds(self.conf)
        for vm in vm_setup:
            openstack_api.compute.delete_server(creds, vm["instance"])

