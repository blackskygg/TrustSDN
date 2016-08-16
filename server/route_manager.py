import json
from ryu.base import app_manager
from trustsdn.server.user_manager import UserManager
import trustsdn.topology.api as tapi
import pdb


class ConManager(app_manager.RyuApp):
    
    """ this class manages the per-tanent connectivity status"""
    def __init__(self, *args, **kwargs):
        super(ConManager, self).__init__(*args, **kwargs)
        self.con = {}             #{mac=>[macs]}
        self.mac_to_port = {}        #maps (vid,mac) to (dpid, port)
        self.flooding_rules = {}  #dpid=>{macs=>{endps, midps}}
        self.flow_path = {} #src_dpid=>{dst_dpid=>[(dpid, outp)]}
    def prepare(self, manager, controller):
        self.usr_manager = manager
        self.cntl = controller
        self.load_config()

    #to be changed to BFS
    def search_path(self, path, cur_dpid, dst_dpid, mark):
        mark[cur_dpid] = True
        if cur_dpid == dst_dpid:
                return True

        for port, next_dpid in self.topo[cur_dpid]["out"].items():
            path.append((cur_dpid, int(port)))
            if next_dpid not in mark and \
            self.search_path(path, next_dpid, dst_dpid, mark):
                return True
            path.pop()
            
        return False
        
    def gen_flow_path(self):
        for src_dpid in self.usr_manager.dpids:
            self.flow_path.setdefault(src_dpid, {})
            for dst_dpid in self.usr_manager.dpids:
                path = []
                self.flow_path[src_dpid].setdefault(dst_dpid, path)
                self.search_path(path, src_dpid, dst_dpid, {})

        print(json.dumps(self.flow_path, indent = 1))
    
    def gen_flooding_flows(self):
        """setup the "base" flooding flows and grps, this will run only once """
        for dst_dpid in self.usr_manager.dpids:
            self.flooding_rules.setdefault(dst_dpid, {})
            for vid_mac, info in self.mac_to_port.items():
                src_dpid = info["dpid"]
                endps = []
                if dst_dpid in self.flood_path[src_dpid]:
                    midps = [p for p in self.flood_path[src_dpid][dst_dpid]]
                else:
                    midps = []
                    
                self.flooding_rules[dst_dpid].setdefault(vid_mac, {"midps": midps,
                                                              "endps": endps})
                self.cntl.setup_flooding_flow(dst_dpid, vid_mac, midps, endps)


    def _add_mac_info(self, dpid, port, vid):
        mac = self.topo[dpid]["in"][str(port)]
        info = {"dpid":dpid, "port":port}
        self.mac_to_port.setdefault((vid, mac), info)
        
    def load_config(self):
        with open("../server/topo.json", "r") as f:
            self.topo = json.load(f)  #{dpid=>{in:{port=>mac}, out:{port=>dpid}}}

        with open("../server/path.json", "r") as f:
            self.flood_path = json.load(f)  #{dpid=>{dpid=>[outports]}}

        for dpid, vlan_list in self.usr_manager.vlan_to_port.items():
            for vid, ports in vlan_list.items():
                for port in ports[0]:
                    self._add_mac_info(dpid, port, vid)
                    
    def add_route(self, dpid1, port1, dpid2, port2, vid):
        mac1 = self.topo[dpid1]["in"][port1]
        mac2 = self.topo[dpid2]["in"][port2]

        #update flooding_group
        endps = self.flooding_rules[dpid2][(vid, mac1)]["endps"]
        midps = self.flooding_rules[dpid2][(vid, mac1)]["midps"]
        endps.append(int(port2))
        self.cntl.mod_flooding_group(dpid2, (vid, mac1), midps, endps, add = False)

        endps = self.flooding_rules[dpid1][(vid, mac2)]["endps"]
        midps = self.flooding_rules[dpid1][(vid, mac2)]["midps"]
        endps.append(int(port1))
        self.cntl.mod_flooding_group(dpid1, (vid, mac2), midps, endps, add = False)

        #add flow_paths
        for dpid, op in self.flow_path[dpid1][dpid2]:
            self.cntl.add_normal_flow(dpid, mac1, mac2, vid, int(op))
        self.cntl.add_normal_flow(dpid2, mac1, mac2,
                                  vid, int(port2), popvlan = True)

        for dpid, op in self.flow_path[dpid2][dpid1]:
            self.cntl.add_normal_flow(dpid, mac2, mac1, vid, int(op))
        self.cntl.add_normal_flow(dpid1, mac2, mac1,
                                  vid, int(port1), popvlan = True)

        
    def del_route(self, dpid1, port1, dpid2, port2, vid):
        mac1 = self.topo[dpid1]["in"][port1]
        mac2 = self.topo[dpid2]["in"][port2]

        #update flooding_group
        endps = self.flooding_rules[dpid2][(vid, mac1)]["endps"]
        midps = self.flooding_rules[dpid2][(vid, mac1)]["midps"]
        try:
            endps.remove(int(port2))
        except ValueError:
            pass
        self.cntl.mod_flooding_group(dpid2, (vid, mac1), midps, endps, add = False)

        endps = self.flooding_rules[dpid1][(vid, mac2)]["endps"]
        midps = self.flooding_rules[dpid1][(vid, mac2)]["midps"]
        try:
            endps.remove(int(port1))
        except ValueError:
            pass
        self.cntl.mod_flooding_group(dpid1, (vid, mac2), midps, endps, add = False)

        #add flow_paths
        self.cntl.del_normal_flow(dpid1, mac1, mac2, vid)
        self.cntl.del_normal_flow(dpid2, mac2, mac1, vid)
