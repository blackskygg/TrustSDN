from ryu.app.wsgi import WSGIApplication
from ryu.app.rest_topology import TopologyController
from ryu.base import app_manager
from ryu.lib import dpid as dpid_lib

from trustsdn.topology import api
from trustsdn.server.user_manager import UserManager

import json
import pdb
from webob import Response


class TrustSDNAPI(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication,
        'user_manager': UserManager
    }

    def __init__(self, *args, **kwargs):
        super(TrustSDNAPI, self).__init__(*args, **kwargs)

        wsgi = kwargs['wsgi']
        auth = kwargs['user_manager']

        self.name = 'trustsdn'
        self.data = { 'trust_sdn_api': self,
                      'topology_api_app':self,
                      'auth':auth }

        wsgi.register(TrustSDNController, self.data)

class TrustSDNController(TopologyController):
    def __init__(self, req, link, data, **config):
        super(TrustSDNController, self).__init__(req, link, data, **config)
        self.trust_sdn_api = data['trust_sdn_api']
        self.auth = data['auth']

    def _switches(self, req, **kwargs):
        user = self.auth.get_user(req, **kwargs)
        type = user.user_type
        if type == "common":
            vdps = user.switches
        elif type == "god" or type == "manager":
            vdps = None


        switches = api.get_switch(self.trust_sdn_api, vdps, type)
        body = json.dumps([switch.to_dict() for switch in switches], indent = 2)
        return Response(content_type='application/json', body=body)

    def _links(self, req, **kwargs):
        user = self.auth.get_user(req, **kwargs)
        type = user.user_type

        if type == "common":
            return Response(content_type=Response(content_type='application/json', body="Permission Denied!"))
        elif type == "god" or type == "manager":
            links = api.get_link(self.trust_sdn_api)
            body = json.dumps([link.to_dict() for link in links], indent = 2)
            return Response(content_type='application/json', body=body)

    def _hosts(self, req, **kwargs):
        user = self.auth.get_user(req, **kwargs)
        type = user.user_type
        if type == "common":
            vdps = user.switches
        elif type == "god" or type == "manager":
            vdps = None

        hosts = api.get_host(self.trust_sdn_api, vdps, type)
        body = json.dumps([host.to_dict() for host in hosts], indent = 2)
        return Response(content_type='application/json', body=body)


