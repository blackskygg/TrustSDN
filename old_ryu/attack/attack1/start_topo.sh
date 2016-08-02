#!/bin/bash
#start topo
gnome-terminal -e 'mn --custom mal_vlan.py --topo=mal_topo --switch ovs,protocols=OpenFlow14  --controller=remote'&
#start controller
ryu-manager --observe-links --verbose ../../gui_topology/gui_topology.py vlan_14.py



