from mininet.topo import Topo

class MyTopo( Topo ):
    "test topology 0"

    def __init__( self ):
        # Initialize topology
        Topo.__init__( self )

        #add switches
        s1 = self.addSwitch('s1', dpid="1")
        s2 = self.addSwitch('s2', dpid="2")

        #add hosts
        vm1 = self.addHost('vm1', ip="10.0.0.1", mac="00:00:00:00:00:01")
        vm2 = self.addHost('vm2', ip="10.0.0.2", mac="00:00:00:00:00:02")
        vm3 = self.addHost('vm3', ip="10.0.0.3", mac="00:00:00:00:00:03")
        vm4 = self.addHost('vm4', ip="10.0.0.4", mac="00:00:00:00:00:04")
        vm5 = self.addHost('vm5', ip="10.0.0.11", mac="00:00:00:00:01:01")
        vm6 = self.addHost('vm6', ip="10.0.0.12", mac="00:00:00:00:01:02")
        vm7 = self.addHost('vm7', ip="10.0.0.13", mac="00:00:00:00:01:03")                
        vm8 = self.addHost('vm8', ip="10.0.0.14", mac="00:00:00:00:01:04")
        vmx = self.addHost('vmx', ip="10.0.0.128", mac="00:00:00:00:02:01")

        # Add links
        self.addLink(s1, s2, port1 = 5, port2 = 5)
        
        self.addLink(vm1, s1, port2 = 1)
        self.addLink(vm2, s1, port2 = 2)
        self.addLink(vm3, s1, port2 = 3)
        self.addLink(vm4, s1, port2 = 4)

        self.addLink(vm5, s2, port2 = 1)
        self.addLink(vm6, s2, port2 = 2)
        self.addLink(vm7, s2, port2 = 3)
        self.addLink(vm8, s2, port2 = 4)

        self.addLink(vmx, s1, port2 = 6)


topos = { 'mal_topo': ( lambda: MyTopo() ) }
