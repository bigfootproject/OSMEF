#!/usr/bin/python

import sys

numvms = int(sys.argv[1])

out = '''
[description]
name = local{0}
# Shuffle size in GB
total_shuffle_size = 10
num_vms = {0}'''.format(numvms)

vmtext = '''

[vm{}]
zone = zone_perf:bigfoot1
num_mappers = 1
num_reducers = 1'''

for i in range(numvms):
        out += vmtext.format(i + 1)

open("local{0}.scen".format(numvms), "w").write(out)
