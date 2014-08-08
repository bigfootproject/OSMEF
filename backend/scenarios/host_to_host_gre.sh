#!/bin/bash

set -x
set -e

source scenarios/common.def

OUT_DIR=$BASE_OUT_DIR/host_to_host_gre

mkdir -p $OUT_DIR

cat > /tmp/gre_tunnel.sh << EOF
#!/bin/sh
ip tunnel add gre_if0 mode gre remote 192.168.46.20 local 192.168.46.11 ttl 255
ip link set gre_if0 up
ip addr add 192.168.1.200/24 dev gre_if0
EOF

cat > /tmp/gre_tunnel_peer.sh << EOF
#!/bin/sh
ip tunnel add gre_if0 mode gre remote 192.168.46.11 local 192.168.46.20 ttl 255
ip link set gre_if0 up
ip addr add 192.168.1.201/24 dev gre_if0
EOF

scp -i ~/.ssh/osmef_key /tmp/gre_tunnel.sh venzano@192.168.46.11:/tmp
ssh -t -i ~/.ssh/osmef_key venzano@192.168.46.11 sudo sh /tmp/gre_tunnel.sh

scp -i ~/.ssh/osmef_key /tmp/gre_tunnel_peer.sh venzano@192.168.46.20:/tmp
ssh -t -i ~/.ssh/osmef_key venzano@192.168.46.20 sudo sh /tmp/gre_tunnel_peer.sh

for p in $C_SEQ_JAIN; do
	echo "Running with $p concurrency"
	./osmef.py --out_dir $OUT_DIR -o json btc_host_if -d $D -n "BTC bigfoot2 bigfooteb GRE $D seconds, $p concurrency" -c$p $USER@192.168.46.11 192.168.1.200 $USER@192.168.46.20
done




