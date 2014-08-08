#!/usr/bin/python3

import math
from pprint import pprint

V = 20  # n. of VMs
H = 6  # n. of physical hosts

SAME_HOST_BW = 10
DIFF_HOST_BW = 1


def count_comb(n, k):
    ''' Counts the ways k object can be put in n containers. '''
    return math.factorial(n + k - 1) / (math.factorial(k) * math.factorial(n - 1))


def binomial(n, k):
    return int(math.factorial(n) / (math.factorial(k) * math.factorial(n - k)))


def calc_bw(comb):
    phys_bw = sum([DIFF_HOST_BW for x in comb if x > 0]) - 1
    return sum([binomial(x, 2) * SAME_HOST_BW for x in comb if x > 1]) + phys_bw


def gen_new_comb(balls, boxes):
    if balls == 0:
        yield [0] * boxes
        return
    if boxes == 1:
        yield [balls]
        return
    for p in range(0, balls + 1):
        for t in ([p] + d for d in gen_new_comb(balls - p, boxes - 1)):
            yield t
#        yield from ([p] + d for d in gen_new_comb(balls - p, boxes - 1))


combinations = int(count_comb(H, V))
print("There are {} possible combinations".format(combinations))

start_comb = [0] * H
start_comb[0] = V

res = []
for comb in gen_new_comb(V, H):
#    print(comb)
    bw = calc_bw(comb)
    res.append([bw, comb])

if len(res) != combinations:
    print("Generated {} combinations, but {} were expected".format(len(res), combinations))
else:
    res.sort(key=lambda x: x[0], reverse=True)
    pprint(res[:10])
    pprint(res[-10:])
