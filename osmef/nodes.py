class Mapper:
    def __init__(self):
        self.port = 0
        self.max_incoming_conn = 0
        self.reducer_sizes = []
        self.ip = ""

    def to_str(self):
        s = "{},{},{}".format(self.max_incoming_conn, self.port, len(self.reducer_sizes))
        for r in self.reducer_sizes:
            s += ",{}".format(r)
        return s


class Reducer:
    def __init__(self):
        self.max_outgoing_connections = 0
        self.mapper_ips = []

    def to_str(self):
        s = "{},{}".format(self.max_outgoing_connections, len(self.mapper_ips))
        for m in self.mapper_ips:
                s += ",{},{}".format(m[1], m[0])  # port,ip,port,ip,...
        return s
