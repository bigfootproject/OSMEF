#!/bin/bash

PYTHONPATH=../..
for i in `seq 2 50`; do ../../osmef.py -s local${i}_1tb -d; done