#!/bin/bash

if [ -z $1 ]; then
	DIR=/tmp
else
	DIR=.
fi

CC=`which gcc`
if [ -z $CC ]; then
	echo "No gcc available"
	exit
fi

gcc -Wall $DIR/worker.c -pthread -o $DIR/worker
md5sum $DIR/worker.c > $DIR/osmef_worker_version

