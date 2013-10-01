#!/bin/bash

set -e
set -x

source scenarios/common.def

if [ z"$1" = z1 ]; then
	M=1
elif [ z"$1" = z2 ]; then
	M=2
elif [ z"$1" = z3 ]; then
	M=3
elif [ z"$1" = z4 ]; then
	M=4
else
	echo "Select one of:"
	echo " 1 - Two VMs on the same host, same tenant"
	echo " 2 - Two VMs on different hosts, same tenant"
	echo " 3 - Two VMs on the same host, different tenants"
	echo " 4 - Two VMs on the different hosts, different tenants"
	exit
fi

OUT_DIR=$BASE_OUT_DIR/vm_to_vm_jain_$M

nova_init

if [ $M -eq 1 ]; then # M=1 -- Two VMs on the same host, same tenant
	MODE="same host, same tenant"
	run_instance single osmef_test_1
	run_instance single osmef_test_2
elif [ $M -eq 2 ]; then # M=2 -- Two VMs on different hosts, same tenant
	MODE="different host, same tenant"
	run_instance single osmef_test_1
	run_instance zone2 osmef_test_2
elif [ $M -eq 3 ]; then # M=3 -- Two VMs on different hosts, same tenant
	MODE="same host, different tenant"
	run_instance single osmef_test_1
	goto_user venzano
	run_instance single osmef_test_2
elif [ $M -eq 4 ]; then
	MODE="different host, different tenant"
	run_instance single osmef_test_1
	goto_user venzano
	run_instance zone2 osmef_test_2
fi

if [ $M -eq 3 -o $M -eq 4 ]; then 
	goto_user admin
	quantum floatingip-associate $FLOATINGIP_ID $(get_quantum_port osmef_test_1)
	TEST1_IP=$FLOATINGIP
	goto_user venzano
	quantum floatingip-associate c0430efe-6cdf-4dbc-8108-a8487ce1788c $(get_quantum_port osmef_test_2)
	TEST2_IP=192.168.45.18
else
	goto_user admin
	quantum floatingip-associate $FLOATINGIP_ID $(get_quantum_port osmef_test_1)
	TEST1_IP=$FLOATINGIP
	quantum floatingip-associate 0a854cc7-e1db-4d21-a6e6-f00ae8621672 $(get_quantum_port osmef_test_2)
	TEST2_IP=192.168.45.17
fi

echo "Sleeping to allow VM boot"
sleep 60

if [ $M -eq 1 -o $M -eq 2 ]; then 
	VMIP=`get_vm_internal_ip osmef_test_1`
else
	VMIP=$TEST1_IP
fi

install_deps $FLOATINGIP
install_deps $TEST2_IP

increase_ssh_limit $FLOATINGIP
increase_ssh_limit $TEST2_IP

mkdir -p $OUT_DIR

for p in $C_SEQ_JAIN; do
	echo "Running with $p concurrency"
	./osmef.py --out_dir $OUT_DIR -o json btc_host_if -d$D -n "VM to VM, $MODE, $D seconds, $p concurrency" -c$p ubuntu@$TEST1_IP $VMIP ubuntu@$TEST2_IP
done

if [ $M -eq 3 -o $M -eq 4 ]; then 
	goto_user admin
	delete_instance osmef_test_1
	goto_user venzano
	delete_instance osmef_test_2
else
	delete_instance osmef_test_1
	delete_instance osmef_test_2
fi

