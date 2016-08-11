import logging

import json
import ast
import pdb
from webob import Response

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import ofproto_v1_2
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ofproto_v1_4
from ryu.lib import ofctl_v1_0
from ryu.lib import ofctl_v1_2
from ryu.lib import ofctl_v1_3
from ryu.lib import ofctl_v1_4
from ryu.app.wsgi import ControllerBase, WSGIApplication
from ryu.app.ofctl_rest import StatsController
from trustsdn.server.user_manager import UserManager
from trustsdn.server.route_manager import ConManager
from trustsdn.server.vlan_14 import Vlan14
import trustsdn.topology.api as tapi

LOG = logging.getLogger('trustsdn.server.ofctl_rest')

# supported ofctl versions in this restful app
supported_ofctl = {
    ofproto_v1_0.OFP_VERSION: ofctl_v1_0,
    ofproto_v1_2.OFP_VERSION: ofctl_v1_2,
    ofproto_v1_3.OFP_VERSION: ofctl_v1_3,
    ofproto_v1_4.OFP_VERSION: ofctl_v1_4
}

def stats_method(translate):
    def _stats_method(method):
        def wrapper(self, req, vdpid, *args, **kwargs):
            user = self.manager.get_user(req, **kwargs)
            usr_type = user.user_type

            #managers are not interested in stats
            if usr_type == 'manager':
                return Response(status=404)

            if req.body == '':
                data = {}
            else:
                try:
                    data = ast.literal_eval(req.body)

                except SyntaxError:
                    LOG.debug('invalid syntax %s', req.body)
                    return Response(status=400)
            try:
                if type(vdpid) == str and not vdpid.isdigit():
                    raise ValueError
                if usr_type != "god":
                    if str(vdpid) not in user.switches:
                        raise ValueError
               
                if usr_type != "god":
                    dpid = user.switches[str(vdpid)]["real"]
                else:
                    dpid = vdpid

                dp = self.dpset.get(int(dpid))
            except:
                return Response(content_type='application/json', body="Wrong vdpid!")
            

            if dp is None:
                return Response(status=404)

            _ofp_version = dp.ofproto.OFP_VERSION

            _ofctl = supported_ofctl.get(_ofp_version, None)
            if _ofctl is not None:
                kwargs['user'] = user
                ret = method(self, data, dp, _ofctl, *args, **kwargs)
            else:
                LOG.debug('Unsupported OF protocol')
                return Response(status=501)

            ret = translate(ret, **kwargs)
            body = json.dumps(ret, indent = 2)
            return Response(content_type='application/json', body=body)

        return wrapper
    return _stats_method


class TrustSDNStatsController(StatsController):
    def __init__(self, req, link, data, **config):
        super(TrustSDNStatsController, self).__init__(req, link, data, **config)
        self.manager = data['manager']
        self.app = data['app']
        self.con_manager = data['con_manager']
    
    def translate_flow_stats(flows, **kwargs):
        user = kwargs['user']
        return user.translator.translate_flows(flows)

    def translate_group_desc(group, **kwargs):
        user = kwargs['user']
        return user.translator.translate_groups(group)

    @stats_method(translate_group_desc)
    def get_group_desc(self, data, dp, ofctl, **kwargs):
        return ofctl.get_group_desc(dp, self.waiters)

    @stats_method(translate_flow_stats)
    def get_flow_stats(self, data, dp, ofctl, *args, **kwargs):
        return ofctl.get_flow_stats(dp, self.waiters, data)

    def connect_hosts(self, req, vdpid1, vport1, vdpid2, vport2, **_kwargs):
        user = self.manager.get_user(req, **_kwargs)

        try:
            dpid1, port1 = user.translator.translate_dpid_port(vdpid1, vport1)
            dpid2, port2 = user.translator.translate_dpid_port(vdpid2, vport2)
        except:
            body="Permission denied!"
        else:
            vid = user.vlan_vid
            self.con_manager.add_route(dpid1, port1, dpid2, port2, vid)
            body="Success!"
            
        return Response(content_type='application/json', body=body)

    def disconnect_hosts(self, req, vdpid1, vport1, vdpid2, vport2, **_kwargs):
        user = self.manager.get_user(req, **_kwargs)

        try:
            dpid1, port1 = user.translator.translate_dpid_port(vdpid1, vport1)
            dpid2, port2 = user.translator.translate_dpid_port(vdpid2, vport2)
        except:
            body="Permission denied!"
        else:
            vid = user.vlan_vid
            self.con_manager.del_route(dpid1, port1, dpid2, port2, vid)
            body="Success!"
            
        return Response(content_type='application/json', body=body)


class TrustSDNRestStatsApi(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION,
                    ofproto_v1_2.OFP_VERSION,
                    ofproto_v1_3.OFP_VERSION,
                    ofproto_v1_4.OFP_VERSION]
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication,
        'user_manager' : UserManager,
        'con_manager' : ConManager
    }

    def __init__(self, *args, **kwargs):
        super(TrustSDNRestStatsApi, self).__init__(*args, **kwargs)
        self.dpset = kwargs['dpset']
        wsgi = kwargs['wsgi']
        self.waiters = {}
        self.data = {}
        self.data['dpset'] = self.dpset
        self.data['waiters'] = self.waiters
        self.data['manager'] = kwargs['user_manager']
        self.data['con_manager'] = kwargs['con_manager']
        self.data['app'] = self
        mapper = wsgi.mapper

        wsgi.registory['TrustSDNStatsController'] = self.data
        path = '/stats'

        uri = path + '/flow/{vdpid}'
        mapper.connect('stats', uri,
                       controller=TrustSDNStatsController, action='get_flow_stats',
                       conditions=dict(method=['GET', 'POST']))

        uri = path + '/groupdesc/{vdpid}'
        mapper.connect('stats', uri,
                       controller=TrustSDNStatsController, action='get_group_desc',
                       conditions=dict(method=['GET']))


        #find a route from d1p1 to d2p2
        uri = '/config/connect/{vdpid1}/{vport1}/{vdpid2}/{vport2}'
        mapper.connect('config', uri,
                       controller=TrustSDNStatsController, action='connect_hosts',
                       conditions=dict(method=['GET', 'POST']))

        #delete the route from d1p1 to d2p2
        uri = '/config/disconnect/{vdpid1}/{vport1}/{vdpid2}/{vport2}'
        mapper.connect('config', uri,
                       controller=TrustSDNStatsController,
                       action='disconnect_hosts',
                       conditions=dict(method=['GET', 'POST']))



    @set_ev_cls([ofp_event.EventOFPStatsReply,
                 ofp_event.EventOFPDescStatsReply,
                 ofp_event.EventOFPFlowStatsReply,
                 ofp_event.EventOFPAggregateStatsReply,
                 ofp_event.EventOFPTableStatsReply,
                 ofp_event.EventOFPTableFeaturesStatsReply,
                 ofp_event.EventOFPPortStatsReply,
                 ofp_event.EventOFPQueueStatsReply,
                 ofp_event.EventOFPQueueDescStatsReply,
                 ofp_event.EventOFPMeterStatsReply,
                 ofp_event.EventOFPMeterFeaturesStatsReply,
                 ofp_event.EventOFPMeterConfigStatsReply,
                 ofp_event.EventOFPGroupStatsReply,
                 ofp_event.EventOFPGroupFeaturesStatsReply,
                 ofp_event.EventOFPGroupDescStatsReply,
                 ofp_event.EventOFPPortDescStatsReply
                 ], MAIN_DISPATCHER)
    def stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath

        if dp.id not in self.waiters:
            return
        if msg.xid not in self.waiters[dp.id]:
            return
        lock, msgs = self.waiters[dp.id][msg.xid]
        msgs.append(msg)

        flags = 0
        if dp.ofproto.OFP_VERSION == ofproto_v1_0.OFP_VERSION:
            flags = dp.ofproto.OFPSF_REPLY_MORE
        elif dp.ofproto.OFP_VERSION == ofproto_v1_2.OFP_VERSION:
            flags = dp.ofproto.OFPSF_REPLY_MORE
        elif dp.ofproto.OFP_VERSION >= ofproto_v1_3.OFP_VERSION:
            flags = dp.ofproto.OFPMPF_REPLY_MORE

        if msg.flags & flags:
            return
        del self.waiters[dp.id][msg.xid]
        lock.set()

    @set_ev_cls([ofp_event.EventOFPSwitchFeatures,
                 ofp_event.EventOFPQueueGetConfigReply], MAIN_DISPATCHER)
    def features_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath

        if dp.id not in self.waiters:
            return
        if msg.xid not in self.waiters[dp.id]:
            return
        lock, msgs = self.waiters[dp.id][msg.xid]
        msgs.append(msg)

        del self.waiters[dp.id][msg.xid]
        lock.set()
