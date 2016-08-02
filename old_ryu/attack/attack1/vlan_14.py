from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_4
from ryu.lib.packet import packet
from ryu.lib.packet import vlan
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
import json
import pdb

VLAN_TAG_TBL  = 0
FLOOD_TBL = 1

class Vlan14(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Vlan14, self).__init__(*args, **kwargs)
        
        #dict{dpid=>dict{vlan=>list[list[end_ports], list[mid_ports]]}}
        self.vlan_to_port = {}
        self.get_vlan_ports_info("vlan_conf.json")

    def get_vlan_ports_info(self, filename):
        f = open(filename, "r")
        self.vlan_to_port = json.load(f)
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

	print datapath.id

        #setup vlan_tag flows
        #
        for vid in self.vlan_to_port[str(datapath.id)]:
            for port in self.vlan_to_port[str(datapath.id)][vid][0]:
                match = parser.OFPMatch(in_port = port)
                actions = [parser.OFPActionPushVlan(),
                           parser.OFPActionSetField(vlan_vid = 0x1000 | int(vid))]
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                        parser.OFPInstructionGotoTable(FLOOD_TBL)]
                mod = parser.OFPFlowMod(datapath, match = match,
                                        instructions = inst, priority = 1,
                                        table_id = VLAN_TAG_TBL)
                datapath.send_msg(mod)
                
        match = parser.OFPMatch()
        inst = [parser.OFPInstructionGotoTable(FLOOD_TBL)]
        mod = parser.OFPFlowMod(datapath, match = match, instructions = inst,
                                priority = 0, table_id = VLAN_TAG_TBL)
        datapath.send_msg(mod)

        
        #setup flooding groups and flows
        cnt = 0
        for vid in self.vlan_to_port[str(datapath.id)]:
            match = parser.OFPMatch(vlan_vid = 0x1000 | int(vid))
            buckets = []
            
            #construct bucket for end ports
            for port in self.vlan_to_port[str(datapath.id)][vid][0]:
                actions = [parser.OFPActionPopVlan()]
                actions.append(parser.OFPActionOutput(port))
                buckets.append(parser.OFPBucket(actions = actions))

            #construct bucket for mid ports
            for port in self.vlan_to_port[str(datapath.id)][vid][1]:
                actions = []
                actions.append(parser.OFPActionOutput(port))
                buckets.append(parser.OFPBucket(actions = actions))

            #and report this flood to the controller
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
            buckets.append(parser.OFPBucket(actions = actions))

            #delete the old(if any), and add the flooding group for this vid
            grp_mod = parser.OFPGroupMod(datapath, ofproto.OFPGC_DELETE,
                                          group_id = cnt)
            datapath.send_msg(grp_mod)
            grp_mod = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD,
                                         ofproto.OFPGT_ALL, cnt, buckets)
            datapath.send_msg(grp_mod)

            #add the flow for vlan_vid = vid
            actions = [parser.OFPActionGroup(cnt)]
            self.add_flow(datapath, 0, match, actions)
            
            cnt = cnt + 1
            
        # install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)


    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst, table_id = FLOOD_TBL)
        datapath.send_msg(mod)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        if len(pkt.get_protocols(vlan.vlan)) != 0:
            vln =pkt.get_protocols(vlan.vlan)[0]
        else:
            return

        dst = eth.dst
        src = eth.src

        vid = vln.vid
        dpid = datapath.id

        self.logger.info("packet in %s %s %s %s %s", dpid, src, dst, in_port, vid)

        actions = []
	try:
	    if in_port not in self.vlan_to_port[str(dpid)][str(vid)][1]:
            	actions = [parser.OFPActionPopVlan()]
	except:
	    pass
        actions.append(parser.OFPActionOutput(in_port))
        match = parser.OFPMatch(eth_dst=src, vlan_vid=0x1000 | int(vid))
        self.add_flow(datapath, 2, match, actions)
            
