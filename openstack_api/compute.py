import novaclient.v1_1.client as nvclient
import novaclient.exceptions
import logging
log = logging.getLogger(__name__)


def create_server(creds, name, flavor, image, host, key):
    nova = nvclient.Client(**creds)
    if not nova.keypairs.findall(name=key):
        raise RuntimeError("SSH key %s not found" % key)
    image = nova.images.find(name=image)
    flavor = nova.flavors.find(name=flavor)
    instance = nova.servers.create(name=name, image=image, flavor=flavor, key_name=key, availability_zone=host)
    return instance


def refresh_instance(creds, instance):
    nova = nvclient.Client(**creds)
    return nova.servers.get(instance.id)


def find_instance(creds, name):
    nova = nvclient.Client(**creds)
    try:
        return nova.servers.find(name=name)
    except novaclient.exceptions.NotFound:
        return None


def delete_server(creds, instance):
    instance.delete()


def get_floating_ip(creds, instance):
    nova = nvclient.Client(**creds)
    flips = nova.floating_ips.list()
    unused = []
    for addr in flips:
        if addr.instance_id == instance.id:
            return addr.ip
        if addr.instance_id is None:
            unused.append(addr)
    if len(unused) == 0:
        log.warning("Creating new floating IP address")
        addr = nova.floating_ips.create()
        unused.append(addr)
    addr = unused.pop()
    log.info("Associating floating IP to VM '%s'" % instance.name)
    instance.add_floating_ip(addr)
    return addr.ip
