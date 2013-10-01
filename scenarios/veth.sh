#!/bin/sh

source scenarios/common.def

set -e

OUT_DIR=$BASE_OUT_DIR/veth

ip netns add test_ns1
ip netns add test_ns2

ip link add name test_veth1 type veth peer name test_veth2
ip link set test_veth1 netns test_ns1
ip link set test_veth2 netns test_ns2
ip netns exec test_ns1 ifconfig test_veth1 192.168.1.101 up
ip netns exec test_ns2 ifconfig test_veth2 192.168.1.102 up

for p in $C_SEQ; do
	echo "Running with $p concurrency"
	./osmef.py --out_dir $OUT_DIR -o json btc -d $D -n "veth $D seconds, $p concurrency" -N -c$p 192.168.1.101 192.168.1.102
done

#ip netns exec test_ns1 nuttcp -S
#ip netns exec test_ns2 nuttcp 192.168.1.101

ip netns exec test_ns1 ip link delete test_veth1

ip netns del test_ns1
ip netns del test_ns2

