class Mapper:
    def __init__(self):
        self.port = 0
        self.max_incoming_conn = 0
        self.all_reducers = None
        self.ip = ""
        self.name = ""

    def to_str(self):
        s = "{},{},{},{}".format(self.name, self.max_incoming_conn, self.port, len(self.all_reducers))
        for r in self.all_reducers:
            s += ",{},{}".format(r.name, r.data_size)
        return s


class Reducer:
    def __init__(self):
        self.max_outgoing_conn = 0
        self.all_mappers = []
        self.name = ""
        self.data_size = 0

    def to_str(self):
        s = "{},{},{}".format(self.name, self.max_outgoing_conn, len(self.all_mappers))
        for m in self.all_mappers:
                s += ",{},{},{}".format(m.name, m.port, m.ip)
        return s
