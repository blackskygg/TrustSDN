#!/bin/bash
#start topo
sudo mn --custom test_vlan.py --topo=test_topo_100 \
      --switch ovs,protocols=OpenFlow14  --controller remote
#start controller
#xterm -e ryu-manager --observe-links --verbose ryu.app.rest_topology  \
#      ryu.app.ofctl_rest vlan_14.py &



