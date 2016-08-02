from mininet.topo import Topo
import json
import pdb

num_tanents = 3
switches_per_tanent = 5
hosts_per_switch = 3

class MyTopo( Topo ):
    """test topology"""
    
    def __init__(self):
        super(MyTopo, self).__init__()
        self.num_branch = [num_tanents, switches_per_tanent]
        self.num_levels = len(self.num_branch)
        self.vid_to_digest = {
            "1": "2C:1B:CD:B6:21:D6:1F:8A:A7:21:4B:96:FC:A8:D0:D6:33:63:CA:C5",
            "2": "FE:DD:44:D7:C2:D9:58:B5:6F:EF:51:C7:4E:2F:AD:AA:B9:1B:A4:0B",
            "3": "79:12:D8:FB:5F:15:16:A8:4E:50:05:A2:A1:DD:1C:D6:3C:EE:99:C6",
            "4": "7D:9F:F8:57:BB:AF:21:51:9C:B0:2D:0D:E3:C8:12:79:D3:CF:D5:B3",
            "5": "27:AB:83:A4:70:C9:6C:6D:AD:80:FD:D7:F9:6F:CE:35:20:3B:60:81",
            "6": "6C:09:8D:D1:A5:D7:CD:50:DE:A9:1E:B9:1F:2D:08:AF:0C:8D:8A:7C",
            "7": "B7:EF:67:DC:65:0D:67:9C:9C:B9:59:43:17:38:9D:DE:8B:43:D7:D3",
            "8": "70:A3:80:8D:E7:79:0F:41:0E:0A:AD:55:F2:E8:E1:DE:E8:05:74:B8"
        }
        self.config_dict = {}

        self.create_switch_tree(0, "", 0)
        self.create_config()
        self.output_config()


    def create_switch_tree(self, level, prev_dpid, index, prev_switch=None):
        curr_dpid = prev_dpid + "%02d"%(index+1)
        switch_name = "s" + curr_dpid

        switch = self.addSwitch(switch_name, dpid = curr_dpid)
        if prev_switch:
            self.addLink(switch, prev_switch)

        if level == self.num_levels:
            for i in range(hosts_per_switch):
                self.attach_hosts(switch, curr_dpid, i)
        else:
            num_switches = self.num_branch[level]
            for i in range(num_switches):
                self.create_switch_tree(level+1, curr_dpid, i, switch)

    def attach_hosts(self, switch, dpid, index):
        host_name = "h" + dpid + "%02d"%(index)
        host = self.addHost(host_name)
        self.addLink(switch, host)

    def create_config(self):
        for vid in range(1, num_tanents+1):
            digest = self.vid_to_digest[str(vid)]
            tanent = self.config_dict[digest] = {}
            self.add_virtual_switches(tanent, vid)
            tanent["vlan_vid"] = vid
            tanent["type"] = "common"

    def add_virtual_switches(self, tanent, vid):
        switches =  tanent["switches"] = {}
        for vdpid in range(1, switches_per_tanent+1):
            vswitch = switches[str(vdpid)] = {}
            dpid = str(int("%02d%02d%02d"%(1,vid,vdpid), base=16))
            
            vswitch["real"] = dpid
            rtov = vswitch["rtov"] = {}
            for port in range(1, hosts_per_switch+2):
                rtov[str(port)] = str(port)
                
            port_type = vswitch["port_type"] = {}
            port_type["1"] = 1
            for port in range(2, hosts_per_switch+2):
                port_type[str(port)] = 0

    def output_config(self):
        with open("eval_config.json", "w") as f:
            json.dump(self.config_dict, f, indent = 2)

topos = { 'eval_topo': ( lambda: MyTopo() ) }
