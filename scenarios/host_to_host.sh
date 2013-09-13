#!/bin/bash

source scenarios/common.def

OUT_DIR=$BASE_OUT_DIR/host_to_host

mkdir -p $OUT_DIR

for p in $C_SEQ_JAIN; do
	echo "Running with $p concurrency"
	./osmef.py --out_dir $OUT_DIR -o json btc -d $D -n "BTC bigfoot2 bigfoot6 $D seconds, $p concurrency" -c$p $USER@192.168.46.11 $USER@192.168.46.15
done




