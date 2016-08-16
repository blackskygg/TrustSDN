from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import dpset
from ryu.ofproto import ofproto_v1_4
from ryu.lib.packet import packet
from ryu.lib.packet import vlan
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from trustsdn.server.authen import Authentication
from trustsdn.server.user_manager import UserManager
from trustsdn.server.route_manager import ConManager
import json
import pdb

class Vlan14(app_manager.RyuApp):
    """ the base controller, it provides machanism, not strategy """
    
    VLAN_TAG_TBL = UserManager.VLAN_TAG_TBL
    JMP_TBL = UserManager.JMP_TBL
    
    _CONTEXTS = {
        'user_manager' : UserManager,
        'con_manager' : ConManager,
    }

    
    def __init__(self, *args, **kwargs):
        super(Vlan14, self).__init__(*args, **kwargs)
        self.usr_manager = kwargs['user_manager']
        self.con_manager = kwargs['con_manager']
        self.dpset = kwargs['dpset']
        
        self.n_ready_dp = 0
        self.dps = {}            #dpid => datapath class
        
        self.flooding_grp = {}   #dict{dpid => {mac => grp_id}}

        self.con_manager.prepare(self.usr_manager, self)
        
    def assign_flooding_grp(self):
        group_cnt = {} #{dpid => {vid => next_group_id}}
        for dpid in self.con_manager.flood_path:
            group_cnt[dpid] = {}
            self.flooding_grp[dpid] = {}

            cnt = 0
            for vid_mac in self.con_manager.mac_to_port:
                vid, mac = vid_mac
                self.flooding_grp[dpid][vid_mac] = cnt
                group_cnt[dpid].setdefault(vid, 0)

                #inform the user_manager of the assignment
                vtable_id = group_cnt[dpid][vid]
                self.usr_manager.set_group_assign(dpid, vid, cnt, vtable_id)
                
                group_cnt[dpid][vid] = vtable_id + 1
                cnt = cnt + 1
    
    def setup_tagging_tbl(self, datapath, dpid):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #setup vlan_tag flows
        for vid in self.usr_manager.vlan_to_port[dpid]:
            for port in self.usr_manager.vlan_to_port[dpid][vid][0]:
                match = parser.OFPMatch(in_port = port)
                actions = [parser.OFPActionPushVlan(),
                           parser.OFPActionSetField(vlan_vid = 0x1000|int(vid))]
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                     actions),
                        parser.OFPInstructionGotoTable(self.JMP_TBL)]
                mod = parser.OFPFlowMod(datapath, match = match,
                                        instructions = inst,
                                        priority = 1, table_id = self.VLAN_TAG_TBL)
                datapath.send_msg(mod)
                
        match = parser.OFPMatch()
        inst = [parser.OFPInstructionGotoTable(self.JMP_TBL)]
        mod = parser.OFPFlowMod(datapath, match = match, instructions = inst,
                                priority = 0, table_id = self.VLAN_TAG_TBL)
        datapath.send_msg(mod)

        
    def setup_jumping_tbl(self, datapath, dpid, n_tables):
        ofproto = datapath.ofproto
        parser =datapath.ofproto_parser

        #assign tables
        self.usr_manager.assign_table(dpid, n_tables // 2)

        #setup jumping tables for vids
        for vid in self.usr_manager.vlan_to_port[dpid]:
            match = parser.OFPMatch(vlan_vid = int(vid) | 0x1000)
            inst = [parser.OFPInstructionGotoTable(self.usr_manager.table_assign[dpid][vid][0])]
            mod = parser.OFPFlowMod(datapath, match = match,
                                    instructions = inst, table_id = self.JMP_TBL)
            datapath.send_msg(mod)

        #setup jumping tables for "others"
        match = parser.OFPMatch()
        inst = [parser.OFPInstructionGotoTable(self.usr_manager.table_assign[dpid]["others"][0])]
        mod  = parser.OFPFlowMod(datapath, match = match, priority = 0,
                                 instructions = inst, table_id = self.JMP_TBL)
        datapath.send_msg(mod)

    def setup_middle_switch(self, datapath, dpid, n_tables):
        self.usr_manager.assign_table(dpid, n_tables // 2)

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_ALL)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                     actions)]
        mod = parser.OFPFlowMod(datapath, match = match,
                                instructions = inst,
                                priority = 1, table_id = self.VLAN_TAG_TBL)
        datapath.send_msg(mod)

        
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = str(datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #prevent configurating one switches twice
        #and remember the relationships between id and datapth
        if self.dps.get(dpid, None):
            return
        else:
            self.dps.setdefault(dpid, datapath)
            self.n_ready_dp = self.n_ready_dp + 1

        if self.usr_manager.vlan_to_port.get(dpid, None):
            self.setup_tagging_tbl(datapath, dpid)
            self.setup_jumping_tbl(datapath, dpid, ev.msg.n_tables)
        else:
            self.setup_middle_switch(datapath, dpid, ev.msg.n_tables)

        #if we've received all the dp's responses, gen the base flows
        if self.n_ready_dp == len(self.con_manager.flood_path):
            self.assign_flooding_grp()
            self.con_manager.gen_flow_path()
            self.con_manager.gen_flooding_flows()


    def add_flow(self, datapath, priority, match, actions, table_id):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst,
                                table_id = table_id)
        datapath.send_msg(mod)


    def add_normal_flow(self, dpid, src_eth, dst_eth, vid, op, popvlan = False):
        datapath = self.dps[dpid]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        if dpid in self.usr_manager.vlan_to_port and \
           vid in self.usr_manager.vlan_to_port[dpid]:
            table_id = self.usr_manager.table_assign[dpid][vid][0]
        else:
            table_id = self.usr_manager.table_assign[dpid]["others"][0]

        match = parser.OFPMatch(vlan_vid = int(vid) | 0x1000,
                                eth_src = src_eth, eth_dst = dst_eth)

        if popvlan:
            actions = [parser.OFPActionPopVlan()]
        else:
            actions = []
        actions.append(parser.OFPActionOutput(op))
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, match = match,
                                instructions = inst, table_id = table_id)
        datapath.send_msg(mod)

    def del_normal_flow(self, dpid, src_eth, dst_eth, vid):
        """ currently it works by modifying the flow action into DROP """
        datapath = self.dps[dpid]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        if vid in self.usr_manager.vlan_to_port[dpid]:
            table_id = self.usr_manager.table_assign[dpid][vid][0]
        else:
            table_id = self.usr_manager.table_assign[dpid]["others"][0]

        match = parser.OFPMatch(vlan_vid = int(vid) | 0x1000,
                                eth_src = src_eth, eth_dst = dst_eth)
        
        actions = []
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, match = match,
                                instructions = inst, table_id = table_id)
        datapath.send_msg(mod)


    def setup_flooding_flow(self, dpid, vid_mac, midps, endps):
        """ setup the "base" flooding flows, will only run once 
        for each mac on each dpid"""

        vid, mac = vid_mac
        datapath = self.dps[dpid]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #add a group
        self._mod_flooding_group(datapath, vid_mac, midps, endps)

        #direct the packets to the group
        grp_id = self.flooding_grp[dpid][vid_mac]
        match = parser.OFPMatch(vlan_vid = int(vid) | 0x1000,
                                eth_src = mac, eth_dst = "ff:ff:ff:ff:ff:ff")
        if vid in self.usr_manager.vlan_to_port[dpid]:
            table_id = self.usr_manager.table_assign[dpid][vid][0]
        else:
            table_id = self.usr_manager.table_assign[dpid]["others"][0]

        actions = [parser.OFPActionGroup(group_id = grp_id)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, match = match,
                                instructions = inst, table_id = table_id)
        datapath.send_msg(mod)


        #and this is for hosts discovery
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath, match = match, instructions = inst,
                                priority = 0, table_id = table_id)
        datapath.send_msg(mod)



    def _mod_flooding_group(self, datapath, vid_mac, midps, endps, add = True):
        dpid = str(datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        grp_id = self.flooding_grp[dpid][vid_mac]
        buckets = []

        for port in midps:
            actions = [parser.OFPActionOutput(port)]
            buckets.append(parser.OFPBucket(actions = actions))

        for port in endps:
            actions = [parser.OFPActionPopVlan()]
            actions.append(parser.OFPActionOutput(port))
            buckets.append(parser.OFPBucket(actions = actions))

        #for debug
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        buckets.append(parser.OFPBucket(actions = actions))
        
        if add:
            #delete the old
            grp_mod = parser.OFPGroupMod(datapath, ofproto.OFPGC_DELETE,
                                     group_id = grp_id)
            datapath.send_msg(grp_mod)
            
            #set the new
            grp_mod = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD,
                                         ofproto.OFPGT_ALL, grp_id, buckets)
        else:
            grp_mod = parser.OFPGroupMod(datapath, ofproto.OFPGC_MODIFY,
                                         ofproto.OFPGT_ALL, grp_id, buckets)

        datapath.send_msg(grp_mod)
            
            
    def mod_flooding_group(self, dpid, vid_mac, midps, endps, add = True):
        """ modify a specific flooding group for mac on dpid """
        datapath = self.dps[dpid]
        self._mod_flooding_group(datapath, vid_mac, midps, endps, add = add)
        

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switchx
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        #get ehter info
        dst = eth.dst
        src = eth.src

        #get vlan info
        if len(pkt.get_protocols(vlan.vlan)) != 0:
            vln =pkt.get_protocols(vlan.vlan)[0]
        else:
            return
        vid = vln.vid

        self.logger.info("packet in %s %s %s %s %s",
                         dpid, src, dst,in_port, vid)

