#!/usr/bin/env python
# By Terry Jones

import sys
import re
import json

def do_query(data, patterns):
    patterns = map(re.compile, patterns)
    retval = []
    return jsongrep(data, patterns, retval)   

def jsongrep(d, patterns, retval):
    try:
        pattern = patterns.pop(0)
    except IndexError:
        retval.append(d)
    else:
        if isinstance(d, dict):
            keys = filter(pattern.match, d.keys())
        elif isinstance(d, list):
            keys = map(int,
                       filter(pattern.match,
                              ['%d' % i for i in range(len(d))]))
        else:
            if pattern.match(str(d)):
                retval.append(d)
            return retval
        for item in (d[key] for key in keys):
            jsongrep(item, patterns[:], retval)

    return retval
