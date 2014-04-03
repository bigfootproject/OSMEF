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
                ret = openstack_api.compute.create_server(creds, vm["name"], vm["flavor"], vm["image"], vm["zone"], vm["key"])
            vm["instance"] = ret
        while True:
            wait = False
            for vm in vm_setup:
                if vm["instance"].status == 'BUILD':
                    vm["instance"] = openstack_api.compute.refresh_instance(creds, vm["instance"])
                    log.debug("VM '%s' not yet ready" % vm["name"])
                    wait = True
            if wait:
                time.sleep(5)
            else:
                log.info("All VMs in status READY")
                break

    def terminate_vms(self, vm_setup):
        creds = openstack_api.get_creds(self.conf)
        for vm in vm_setup:
            openstack_api.compute.delete_server(creds, vm["instance"])

