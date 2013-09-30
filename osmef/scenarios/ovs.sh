#!/bin/bash

source scenarios/common.def

set -e -x

OUT_DIR=$BASE_OUT_DIR/ovs

mkdir -p $OUT_DIR

NS1=test_ns1
NS2=test_ns2

IF1=testif1
IF2=testif2

BR=test_br

EXEC_NS1="sudo ip netns exec $NS1"
EXEC_NS2="sudo ip netns exec $NS2"

sudo ip netns add $NS1
sudo ip netns add $NS2

sudo ovs-vsctl add-br $BR
sudo ovs-vsctl add-port $BR $IF1 -- set interface $IF1 type=internal
sudo ovs-vsctl add-port $BR $IF2 -- set interface $IF2 type=internal

sudo ip link set $IF1 netns $NS1
sudo ip link set $IF2 netns $NS2

$EXEC_NS1 ip addr add 192.168.1.101/24 dev $IF1
$EXEC_NS2 ip addr add 192.168.1.102/24 dev $IF2

$EXEC_NS1 ip link set $IF1 up
$EXEC_NS2 ip link set $IF2 up

$EXEC_NS1 ip link set lo up
$EXEC_NS2 ip link set lo up

$EXEC_NS1 ping -c 2 192.168.1.102

for p in $C_SEQ; do
	echo "Running with $p concurrency"
	sudo ./osmef.py --out_dir $OUT_DIR -o json btc -d $D -n "ovs $D seconds, $p concurrency" -N -c$p 192.168.1.101 192.168.1.102
done

sudo ovs-vsctl del-port $BR $IF1
sudo ovs-vsctl del-port $BR $IF2
sudo ovs-vsctl del-br $BR

sudo ip netns del $NS1
sudo ip netns del $NS2

