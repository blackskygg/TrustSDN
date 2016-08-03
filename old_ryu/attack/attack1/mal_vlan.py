from mininet.topo import Topo

class MyTopo( Topo ):
    "test topology 0"

    def __init__( self ):
        # Initialize topology
        Topo.__init__( self )

        #add switches
        s1 = self.addSwitch('s1', dpid="1")
        s2 = self.addSwitch('s2', dpid="2")
	s3 = self.addSwitch('s3', dpid="3")
	s4 = self.addSwitch('s4', dpid="4")

        #add hosts
        vm1 = self.addHost('vm1', ip="10.0.0.1", mac="00:00:00:00:00:01")
        vm2 = self.addHost('vm2', ip="10.0.0.3", mac="00:00:00:00:00:03")
        vm3 = self.addHost('vm3', ip="10.0.0.3", mac="00:00:00:00:00:02")
        vm4 = self.addHost('vm4', ip="10.0.0.4", mac="00:00:00:00:00:04")
        vm5 = self.addHost('vm5', ip="10.0.0.5", mac="00:00:00:00:00:05")
        vm6 = self.addHost('vm6', ip="10.0.0.6", mac="00:00:00:00:00:06")
        vm7 = self.addHost('vm7', ip="10.0.0.7", mac="00:00:00:00:00:07")                
        vm8 = self.addHost('vm8', ip="10.0.0.8", mac="00:00:00:00:00:08")
	vm9 = self.addHost('vm9', ip="10.0.0.9", mac="00:00:00:00:00:09")

        # Add links
        self.addLink(s1, s2, port1 = 1, port2 = 1)
	self.addLink(s1, s3, port1 = 2, port2 = 1)
	self.addLink(s2, s4, port1 = 2, port2 = 1)
	self.addLink(s3, s4, port1 = 2, port2 = 2)
        
        self.addLink(vm1, s1, port2 = 3)

        self.addLink(vm2, s3, port2 = 3)
        self.addLink(vm3, s3, port2 = 4)

        self.addLink(vm4, s2, port2 = 3)
        self.addLink(vm5, s2, port2 = 4)

        self.addLink(vm6, s3, port2 = 5)
        self.addLink(vm7, s3, port2 = 6)

	self.addLink(vm8, s4, port2 = 3)
        self.addLink(vm9, s4, port2 = 4)


topos = { 'mal_topo': ( lambda: MyTopo() ) }
