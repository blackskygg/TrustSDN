#!/bin/bash
#start topo
sudo mn --custom ppt_vlan.py --topo=mytopo \
      --switch ovs,protocols=OpenFlow14  --controller remote 
#start controller
#xterm -e ryu-manager --observe-links --verbose ryu.app.rest_topology  \
#      ryu.app.ofctl_rest vlan_14.py &



