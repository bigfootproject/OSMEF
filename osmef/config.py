import ConfigParser
import getpass
import os

CONF_FILE = "config.ini"

class Config:
    def __init__(self, cfile):
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(cfile)
        
    def _getopt(self, section, name):
        try:
            return self.config.get(section, name)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return None

    def get_ssh_key(self):
        keyf = self._getopt("ssh", "private_key")
        if not os.path.exists(keyf):
            return None
        else:
            return keyf

    def get_server_namespace(self):
        ns = self._getopt("namespaces", "server_ns")
        if ns == None:
            ns = "test_ns1"
        return ns

    def get_client_namespace(self):
        ns = self._getopt("namespaces", "client_ns")
        if ns == None:
            ns = "test_ns2"
        return ns

conf_store = Config(CONF_FILE)

