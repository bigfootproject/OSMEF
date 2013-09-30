import os
import spur
from config import conf_store

class SshConnection:
    def __init__(self, host):
        if "@" in host:
            self.user, self.host = host.split("@")
        else:
            self.host = host
            self.user = os.getenv("USER")
        self.key = conf_store.get_ssh_key()
        self.conn = None

    def connect(self):
        if self.host == "127.0.0.1" or self.host == "localhost":
            self.conn = spur.LocalShell()
        else:
            self.conn = spur.SshShell(hostname=self.host,
                                username=self.user,
                                private_key_file=self.key,
                                missing_host_key=spur.ssh.MissingHostKey.accept)

    def run(self, cmd, allow_error=False):
        if self.conn == None:
            self.connect()
        result = self.conn.run(cmd, allow_error=allow_error)
        return result.output

