from mininet.topo import Topo


class MyTopo(Topo):

  def __init__(self):

    Topo.__init__(self)

    s1 = self.addSwitch('s1', dpid="1")
    s2 = self.addSwitch('s2', dpid="2")
    s3 = self.addSwitch('s3', dpid="3")
    s4 = self.addSwitch('s4', dpid="4")
    
    vm1 = self.addHost('vm1', ip = "10.0.2.1", mac = "00:00:00:00:02:01")
    vm2 = self.addHost('vm2', ip = "10.0.2.2", mac = "00:00:00:00:02:02")
    vm3 = self.addHost('vm3', ip = "10.0.2.3", mac = "00:00:00:00:02:03")    
    vm4 = self.addHost('vm4', ip = "10.0.2.4", mac = "00:00:00:00:02:04")
    
    vm5 = self.addHost('vm5', ip = "10.0.3.1", mac = "00:00:00:00:03:01")
    vm6 = self.addHost('vm6', ip = "10.0.3.2", mac = "00:00:00:00:03:02")

    vm7 = self.addHost('vm7', ip = "10.0.1.1", mac = "00:00:00:00:01:01")
    vm8 = self.addHost('vm8', ip = "10.0.1.2", mac = "00:00:00:00:01:02")
    vm9 = self.addHost('vm9', ip = "10.0.1.3", mac = "00:00:00:00:01:03")    
    vm10 = self.addHost('vm10', ip = "10.0.1.4", mac = "00:00:00:00:01:04")

    vmx = self.addHost('vmx', ip = "10.0.0.128", mac = "00:00:00:00:00:ff")

    self.addLink(s1, vm1, port1 = 1)
    self.addLink(s1, vm2, port1 = 2)
    
    self.addLink(s2, vm5, port1 = 2)
    self.addLink(s2, vm6, port1 = 1)

    self.addLink(s3, vm3, port1 = 1)
    self.addLink(s3, vm4, port1 = 2)
    self.addLink(s3, vm7, port1 = 3)
    self.addLink(s3, vm8, port1 = 4)
    
    self.addLink(s4, vm9, port1 = 1)
    self.addLink(s4, vm10, port1 = 2)

    self.addLink(s1, s2, port1 = 4, port2 = 3)
    self.addLink(s2, s4, port1 = 4, port2 = 3)
    self.addLink(s4, s3, port1 = 4, port2 = 5)
    self.addLink(s3, s1, port1 = 6, port2 = 3)


topos = {'mytopo': (lambda: MyTopo()) }
