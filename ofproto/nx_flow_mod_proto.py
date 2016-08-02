import ryu.ofproto.ofproto_v1_4 as ofproto
import ryu.ofproto.ofproto_v1_4_parser as parser
import ryu.ofproto.nicira_ext as nx

#struct nx_flow_monitor
_NX_FLOW_MONITOR_PACK_STR0 = 'IIIB'
NX_FLOW_MONITOR_PACK_STR = '!' + _NX_FLOW_MONITOR_PACK_STR0 + ofproto._OFP_MATCH_PACK_STR
NX_FLOW_MONITOR_PACK_STR0 = '!' + _NX_FLOW_MONITOR_PACK_STR0

#struct enum
NXFMF_INITIAL = 1 << 0  #Initially matching flows. 
NXFMF_ADD = 1 << 1      #New matching flows as they are added. 
NXFMF_DELETE = 1 << 2   #Old matching flows as they are removed.
NXFMF_MODIFY = 1 << 3   #Matching flows as they are changed. 
NXFMF_ACTIONS = 1 << 4  #If set actions are included. 
NXFMF_OWN = 1 << 5      #If set include own changes in full. 


class NXFlowMonitorRequestBase(parser.OFPMultipartRequest):
    def __init__(self, datapath, flags, monitor_id, out_port,
                 monitor_flags, table_id, match):
        super(OFPFlowMonitorRequestBase, self).__init__(datapath, flags)
        self.monitor_id = monitor_id
        self.out_port = out_port
        self.monitor_flags = monitor_flags
        self.table_id = table_id
        self.match = match

    def _serialize_stats_body(self):
        offset = ofproto.OFP_MULTIPART_REQUEST_SIZE
        msg_pack_into(ofproto.OFP_FLOW_MONITOR_REQUEST_0_PACK_STR, self.buf,
                      offset, self.monitor_id, self.out_port, self.out_group,
                      self.monitor_flags, self.table_id, self.command)

        offset += ofproto.OFP_FLOW_MONITOR_REQUEST_0_SIZE
        self.match.serialize(self.buf, offset)
