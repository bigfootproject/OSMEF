#!/bin/sh

echo 2 > /proc/sys/vm/overcommit_memory
echo 100 > /proc/sys/vm/overcommit_ratio

