from collections import defaultdict

_f = lambda: defaultdict(_f)


def new():
    return defaultdict(_f)
