#!/bin/bash

set -e
set -x

source scenarios/common.def

OUT_DIR=$BASE_OUT_DIR/vm_localhost_16cpu_jain

nova_init

run_instance single osmef_test

quantum floatingip-associate $FLOATINGIP_ID $(get_quantum_port osmef_test)

# Sleep 40 seconds to allow boot
sleep 50

install_deps $FLOATINGIP

increase_ssh_limit $FLOATINGIP

mkdir -p $OUT_DIR

for p in $C_SEQ_JAIN; do
	echo "Running with $p concurrency"
	./osmef.py --out_dir $OUT_DIR -o json localhost_btc -d$D -n "VM localhost $D seconds, $p concurrency" -c$p ubuntu@$FLOATINGIP
	./osmef.py --out_dir $OUT_DIR -o json localhost_btc -d$D -n "VM localhost $D seconds, $p concurrency" -c$p ubuntu@$FLOATINGIP
	./osmef.py --out_dir $OUT_DIR -o json localhost_btc -d$D -n "VM localhost $D seconds, $p concurrency" -c$p ubuntu@$FLOATINGIP
	./osmef.py --out_dir $OUT_DIR -o json localhost_btc -d$D -n "VM localhost $D seconds, $p concurrency" -c$p ubuntu@$FLOATINGIP
	./osmef.py --out_dir $OUT_DIR -o json localhost_btc -d$D -n "VM localhost $D seconds, $p concurrency" -c$p ubuntu@$FLOATINGIP
done

delete_instance osmef_test

