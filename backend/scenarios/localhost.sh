#!/bin/bash
 
set -x -e

source scenarios/common.def

OUT_DIR=$BASE_OUT_DIR/localhost

HOST=127.0.0.1

mkdir -p $OUT_DIR

for p in $C_SEQ_JAIN; do
	echo "Running with $p concurrency"
	./osmef.py --out_dir $OUT_DIR -o json btc -d $D -n "Bigfoot1 localhost $D seconds, $p concurrency" -c$p $USER@$HOST $USER@$HOST
done


