from ryu.topology import switches
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from trustsdn.topology import event
from trustsdn.server.user_manager import UserManager
import pdb

#redefine switches.port.to_dict to add port_type info
class VPort(switches.Port):
    def __init__(self, dpid, ofproto, ofpport):
        super(VPort, self).__init__(dpid, ofproto, ofpport)
        self.port_type = 0

    def to_dict(self):
        dict = super(VPort, self).to_dict()
        dict.update({'port_type':self.port_type})
        return dict
 
    
class VDataPath(object):
    def __init__(self, dpid):
        self.id = int(dpid)

class VHost(switches.Host):
    def __init__(self, mac, port):
        super(VHost, self).__init__(mac, port)
        self.vid = None

    def to_dict(self):
        dict = super(VHost, self).to_dict()
        dict['vid'] = self.vid
        return dict

class Switches(switches.Switches):
    _CONTEXTS = {
        'user_manager' : UserManager,
    }

    def __init__(self, *args, **kwargs):
        super(Switches, self).__init__(*args, **kwargs)
        self.name = 'vswitches'
        self.is_active = True
        self.link_discovery = True
        self.install_flow = True
        self.explicit_drop = True
        self.lldp_event = hub.Event()
        self.link_event = hub.Event()
        self.threads.append(hub.spawn(self.lldp_loop))
        self.threads.append(hub.spawn(self.link_loop))

        self.usr_manager=kwargs['user_manager']


    def _get_vswitch(self, dpid, vdpid, vswitch):
        vs = switches.Switch(VDataPath(vdpid))
        port_state = self.port_state[dpid]

        # modify port according to the port map
        ofproto = self.dps[dpid].ofproto
        for r, v in vswitch['rtov'].items():
            # physical port
            ofpport = port_state.get(int(r), None)
            if ofpport:
                port = VPort(int(vdpid), ofproto, ofpport)
                # modify physical port no to virtual port no
                # and real name to a pseudonym
                port.port_no = int(v)
                port.port_type = vswitch['port_type'][r]
                port.name = "s%d-eth%d"%(int(vdpid), int(v))
                vs.ports.append(port)
        return vs

    @set_ev_cls(event.EventLinkRequest)
    def link_request_handler(self, req):
        rep = event.EventLinkReply(req.src, None, self.links)
        self.reply_to_request(req, rep)

    # get data of virtual switches
    @set_ev_cls(event.EventSwitchRequest)
    def switch_request_handler(self, req):
        if req.type == "god":
            req.dpid = None
            super(Switches, self).switch_request_handler(req)
            return 
        elif req.type == "manager":
            req.dpid = None
            super(Switches, self).switch_request_handler(req)
            return 
        
        # LOG.debug(req)
        vswitches = req.vdps
        switches_reply = []

        # get all vswitches
        for vdpid, vswitch in vswitches.items():
            dpid = int(vswitch['real'])
            if dpid in self.dps:
                vs = self._get_vswitch(dpid, vdpid, vswitch)
                switches_reply.append(vs)

        rep = event.EventSwitchReply(req.src, switches_reply)
        self.reply_to_request(req, rep)

    @set_ev_cls(event.EventHostRequest)
    def host_request_handler(self, req):
        vhosts = []
        if req.type == "god":
            for mac in self.hosts:
                vhost = VHost(mac, self.hosts[mac].port)
                dpid = vhost.port.dpid
                port_no = vhost.port.port_no
                vhost.vid, x, y = self.usr_manager.port_to_vlan[(dpid, port_no)]
                vhosts.append(vhost)
            rep = event.EventHostReply(req.src, None, vhosts)
            self.reply_to_request(req, rep)
            
        elif req.type == "manager":
            for mac in self.hosts:
                vhost = VHost(mac, self.hosts[mac].port)
                vhost.mac = None
                vhosts.append(vhost)
            rep = event.EventHostReply(req.src, None, vhosts)
            self.reply_to_request(req, rep)
            
        else:
            vswitches = req.vdps
            hosts = []
            for vdpid, vswitch in vswitches.items():
                dpid = int(vswitch["real"])
                hosts = self.hosts.get_by_dpid(int(vswitch["real"]))

                ofproto = self.dps[dpid].ofproto
                port_state = self.port_state[dpid]
            
                for h in hosts:
                    if str(h.port.port_no) in vswitch["rtov"]:
                        ofpport = port_state.get(h.port.port_no, None)

                        #create a virutal port
                        vp = VPort(int(vdpid), ofproto, ofpport)
                        vp.port_no = int(vswitch["rtov"][str(vp.port_no)])
                    
                        #pseudonym
                        vp.name = "s%d-eth%d"%(int(vdpid), vp.port_no)

                        #create a virtual host
                        vh = switches.Host(h.mac, vp)
                        vh.ipv4 = h.ipv4
                        vh.ipv6 = h.ipv6
                    
                        vhosts.append(vh)
 

        rep = event.EventHostReply(req.src, None, vhosts)
        self.reply_to_request(req, rep)

