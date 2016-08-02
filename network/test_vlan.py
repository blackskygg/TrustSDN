from mininet.topo import Topo
import json
import pdb


class MyTopo( Topo ):
    """test topology"""
    
    def __init__( self ):
        # Initialize topology
        Topo.__init__( self )

        self.N_LAYER = [2, 2, 2]
        self.N_HOSTS = 6

        pdb.set_trace()
        self.Switches = {}
        #create switches
        for l1 in range(1, self.N_LAYER[0] + 1):
            switch1 = self.addSwitch('s%d'%(l1),
                                     dpid = "%03d%03d%03d"%(l1,0,0))
            self.Switches['s%d'%(l1)] = switch1
            
            for l2 in range(1, self.N_LAYER[1] + 1):
                switch2 = self.addSwitch('s%d_%d'%(l1, l2),
                                         dpid = "%03d%03d%03d"%(l1,l2,0))
                self.Switches['s%d_%d'%(l1, l2)] = switch2
                
                self.addLink(switch1, switch2,
                             port1 = l2,
                             port2 = self.N_LAYER[2] + 1)
                             
                for l3 in range(1, self.N_LAYER[2] + 1):
                    switch3 = self.addSwitch('s%d_%d_%d'%(l1,l2,l3),
                                             dpid = "%03d%03d%03d"%(l1,l2,l3))
                    self.Switches['s%d_%d_%d'%(l1,l2,l3)] = switch3
                    self.addLink(switch2, switch3,
                                 port1 = l3,
                                 port2 = self.N_HOSTS + 1)

                    self.addhosts(switch3, (l1,l2,l3))

        for i in range(1, self.N_LAYER[0]):
            self.addLink(self.Switches['s%d'%(i)],
                         self.Switches['s%d'%(i + 1)],
                         port1 = self.N_LAYER[1] + 1,
                         port2 = self.N_LAYER[1] + 2)
            
        self.create_config()

    def addhosts(self, switch, index):
        l1, l2, l3 = index
        self.Hosts = {}
        for i in range(1, self.N_HOSTS+1):
            i_tuple = (l1, l2, l3, i)
            host = self.addHost('h%d_%d_%d_%d'%i_tuple,
                                ip="%d.%d.%d.%d"%i_tuple,
                                mac="00:00:%02x:%02x:%02x:%02x"%i_tuple)

            self.Hosts['h%d_%d_%d_%d'%i_tuple] = host
            self.addLink(switch, host, port1 = i)

    def init_custom_switch(self, c, dpid):
        c["switches"][str(int(dpid, base=16))] = {}
        
        switch = c["switches"][str(int(dpid, base=16))]
        switch["real"] = str(int(dpid, base = 16))
        switch["rtov"] = {}
        switch["port_type"] = {}

        return switch
    
    def config_l12(self, c, dpid, layer):
        if layer == 0:
            extra = 2
        else:
            extra = 1
            
        switch = self.init_custom_switch(c, dpid)
        for port in range(1, self.N_LAYER[layer+1] + 1 + extra):
            switch["rtov"][str(port)] = str(port)
            switch["port_type"][str(port)] = 1

    def config_l3(self, c1, c2, dpid):
        switch1 = self.init_custom_switch(c1, dpid)
        switch2 = self.init_custom_switch(c2, dpid)

        for port in range(1, self.N_HOSTS/2 + 1):
            switch1["rtov"][str(port)] = str(port)
            switch1["port_type"][str(port)] = 0

        for port in range(self.N_HOSTS/2 + 1, self.N_HOSTS + 1):
            switch2["rtov"][str(port)] = int(port - self.N_HOSTS/2)
            switch2["port_type"][str(port)] = 0

        switch1["rtov"][str(self.N_HOSTS+1)] = str(self.N_HOSTS/2 + 1)
        switch1["port_type"][str(self.N_HOSTS+1)] = 1
        switch2["rtov"][str(self.N_HOSTS+1)] = str(self.N_HOSTS/2 + 1)
        switch2["port_type"][str(self.N_HOSTS+1)] = 1

        
    def create_config(self):
        config = {}
        
        config["2C:1B:CD:B6:21:D6:1F:8A:A7:21:4B:96:FC:A8:D0:D6:33:63:CA:C5"] = {}
        c1 = config["2C:1B:CD:B6:21:D6:1F:8A:A7:21:4B:96:FC:A8:D0:D6:33:63:CA:C5"]
        c1["type"] = "common"
        c1["vlan_vid"] = 1
        c1["switches"] = {}

        config["FE:DD:44:D7:C2:D9:58:B5:6F:EF:51:C7:4E:2F:AD:AA:B9:1B:A4:0B"] = {}
        c2 = config["FE:DD:44:D7:C2:D9:58:B5:6F:EF:51:C7:4E:2F:AD:AA:B9:1B:A4:0B"]
        c2["type"] = "common"
        c2["vlan_vid"] = 2
        c2["switches"] = {}

        for l1 in range(1, self.N_LAYER[0]+1):
            dpid = "%03d%03d%03d"%(l1,0,0)
            self.config_l12(c1, dpid, 0)
            self.config_l12(c2, dpid, 0)
            
            for l2 in range(1, self.N_LAYER[1]+1):
                dpid = "%03d%03d%03d"%(l1,l2,0)
                self.config_l12(c1, dpid, 1)
                self.config_l12(c2, dpid, 1)
                             
                for l3 in range(1, self.N_LAYER[2]+1):
                    dpid = "%03d%03d%03d"%(l1,l2,l3)
                    self.config_l3(c1, c2, dpid)

        f = open("test_config.json", "w")
        json.dump(config, f, indent = 4)

topos = { 'test_topo_100': ( lambda: MyTopo() ) }
