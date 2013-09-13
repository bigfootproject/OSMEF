#!/bin/bash

set -x
set -e

source scenarios/common.def

OUT_DIR=$BASE_OUT_DIR/vm_host
OUT_DIR2=$BASE_OUT_DIR/host_vm

nova_init

run_instance single osmef_test

quantum floatingip-associate $FLOATINGIP_ID $(get_quantum_port osmef_test)

# Sleep to allow boot
sleep 40

VMIP=`get_vm_internal_ip osmef_test`

echo "Enter sudo password at the right times"
BRIDGE=$(ssh -t -i ~/.ssh/osmef_key $USER@192.168.46.10 sudo cat /etc/libvirt/qemu/`nova show osmef_test | grep instance_name | cut -d\| -f3 | tr -d \ `.xml | grep "target dev='tap" | cut -f2 -d\')
echo "Interface name is $BRIDGE, ready to enter sudo password again to set IP address 10.10.10.100"
ssh -t -i ~/.ssh/osmef_key $USER@192.168.46.10 sudo ip addr add 10.10.10.100/24 dev br-int

install_deps $FLOATINGIP

increase_ssh_limit $FLOATINGIP

TAG=$(ssh -t -i ~/.ssh/osmef_key $USER@192.168.46.10 sudo ovs-vsctl show | grep -n2 $BRIDGE | grep tag | cut -f2 -d: | tr -d ' \r' )
echo "VLAN tag is $TAG"
ssh -t -i ~/.ssh/osmef_key $USER@192.168.46.10 sudo ovs-vsctl set port br-int tag=$TAG

echo "You should get a succesful ping now"
ssh -t -i ~/.ssh/osmef_key $USER@192.168.46.10 ping -c 1 $VMIP

mkdir -p $OUT_DIR

for p in $C_SEQ; do
	echo "Running with $p concurrency"
	./osmef.py --out_dir $OUT_DIR -o json btc_host_if -d$D -n "host to VM $D seconds, $p concurrency" -c$p ubuntu@$FLOATINGIP $VMIP $USER@192.168.46.10
	./osmef.py --out_dir $OUT_DIR2 -o json btc_host_if -d$D -n "VM to host $D seconds, $p concurrency" -c$p $USER@192.168.46.10 10.10.10.100 ubuntu@$FLOATINGIP 
done

ssh -t -i ~/.ssh/osmef_key $USER@192.168.46.10 sudo ovs-vsctl clear port br-int tag
ssh -t -i ~/.ssh/osmef_key $USER@192.168.46.10 sudo ip addr del 10.10.10.100/24 dev br-int

delete_instance osmef_test

