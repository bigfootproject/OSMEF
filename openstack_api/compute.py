import novaclient.v1_1.client as nvclient
import novaclient.exceptions


def create_server(creds, name, flavor, image, zone, key):
    nova = nvclient.Client(**creds)
    if not nova.keypairs.findall(name=key):
        raise RuntimeError("SSH key %s not found" % key)
    image = nova.images.find(name=image)
    flavor = nova.flavors.find(name=flavor)
    instance = nova.servers.create(name=name, image=image, flavor=flavor, key_name=key)
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
