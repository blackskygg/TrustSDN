import json
import logging

LOG = logging.getLogger('trustsdn.server.user_manager')

class Translator(object):
    port_key = {"port", "in_port", "out_port"}
    table_key = {"table_id"}
    group_key = {"group_id"}
    interested_flow_keys = {"priority", "table_id"}
    interested_group_keys = {"type", "group_id"}
    forbidden_keys = {"len", "max_len", "vlan_vid", "length"}

    def __init__(self, user, *args, **kwargs):
        self.user = user

    def real_to_virt(self, content, key, value, vdpid, dpid):
        usr_type = self.user.user_type
        if usr_type == "god" or usr_type  == "manager":
            return
        
        if key in self.port_key:
            #add try to ignore reserved ports
            try:
                content[key] =  self.user.switches[vdpid]["rtov"][str(value)]
            except:
                pass
        elif key in self.table_key:
            vid = self.user.vlan_vid
            new_id = int(value) - int(self.user.manager.table_assign[dpid][vid][0])
            content[key] =  str(new_id)
        elif key in self.group_key:
            vid, new_id = self.user.manager.group_assign[dpid][value]
            content[key] = str(new_id)
        else:
            pass

    def translate_dpid_port(self, vdpid, vport):
        try:
            ##to be optimized
            vdpid = str(int(vdpid))
            vport = str(int(vport))
        
            dpid = self.user.switches[vdpid]["real"]
        except:
            raise KeyError()
            
        port = None
        for rp, vp in self.user.switches[vdpid]["rtov"].items():
            if (vp == vport) and (self.user.switches[vdpid]["port_type"][rp] != 1):
                port = rp
        if not port:
            raise KeyError()

        return (dpid, port)


    def translate_match(self, match, vdpid, dpid):
        for key, value in match.items():
            if key in self.forbidden_keys:
                del match[key]
            else:
                self.real_to_virt(match, key, value, vdpid, dpid)

    def translate_actions(self, actions, vdpid, dpid):
        for action in actions:
            for key, value in action.items():
                if key in self.forbidden_keys:
                    del action[key]
                else:
                    self.real_to_virt(action, key, value, vdpid, dpid)

    def translate_inst(self, insts, vdpid, dpid):
        for inst in insts:
            for key, value in inst.items():
                if key == "actions":
                    self.translate_actions(value, vdpid, dpid)
                elif key in self.forbidden_keys:
                    del inst[key]
                else:
                    self.real_to_virt(inst, key, value, vdpid, dpid)

    def translate_buckets(self, buckets, vdpid, dpid):
        for bucket in buckets:
            for key, value in bucket.items():
                if key == "actions":
                    self.translate_actions(value, vdpid, dpid)
                else:
                    del bucket[key]
    
    def _translate_groups(self, contents, dpid=None, vdpid=None):
        for key, value in contents.items():
            if key == "buckets":
                self.translate_buckets(value, vdpid, dpid)
            elif key in self.interested_group_keys:
                self.real_to_virt(contents, key, value, vdpid, dpid)
            else:
                del contents[key]
    
    def translate_groups(self, contents):
        new_contents = {}
        for dpid, dp_info in contents.items():
            usr_type = self.user.user_type
            new_dp_info = []

            if usr_type == "god" or usr_type  == "manager":
                for rule in dp_info:
                    self._translate_groups(rule, None, None)
                    new_dp_info.append(rule)

                new_contents[dpid] = new_dp_info
            else:
                if dpid not in self.user.manager.dpid_assign:
                    continue
                
                vid = self.user.vlan_vid
                vdpid = str(self.user.manager.dpid_assign[dpid][vid])
                for rule in dp_info:
                    group_id = int(rule["group_id"])
                    dst_vid, dummy = self.user.manager.group_assign[dpid][group_id]
                    if vid == dst_vid:
                        self._translate_groups(rule, vdpid, dpid)
                        new_dp_info.append(rule)
                        
                new_contents[vdpid] = new_dp_info

        return new_contents

    def _translate_flows(self, contents, vdpid, dpid):
        for key,value in contents.items():
            if key ==  "match":
                self.translate_match(value, vdpid, dpid)
            elif key == "instructions":
                self.translate_inst(value, vdpid, dpid)
            elif key in self.interested_flow_keys:
                self.real_to_virt(contents, key, value, vdpid, dpid)
            else:
                del contents[key]

    def translate_flows(self, contents):
        new_contents = {}

        for dpid, dp_info in contents.items():
            usr_type = self.user.user_type
            new_dp_info = []

            if usr_type == "god" or usr_type  == "manager":
                for rule in dp_info:
                    self._translate_flows(rule, None, None)
                    new_dp_info.append(rule)

                new_contents[dpid] = new_dp_info
            else:
                if dpid not in self.user.manager.dpid_assign:
                    continue
                
                vid = self.user.vlan_vid
                vdpid = str(self.user.manager.dpid_assign[dpid][vid])
                for rule in dp_info:
                    low = self.user.manager.table_assign[dpid][vid][0]
                    high = self.user.manager.table_assign[dpid][vid][1]
                    if int(rule["table_id"]) >= low and\
                       int(rule["table_id"]) <= high:
                        self._translate_flows(rule, vdpid, dpid)
                        new_dp_info.append(rule)
                        
                new_contents[vdpid] = new_dp_info

        return new_contents


class User(object):
    def __init__(self, config, manager):
        self.manager = manager
        self.user_type = config['type']
        self.translator = Translator(self)
        if self.user_type != "manager" and self.user_type != "god":
            self.switches = config['switches']
            self.vlan_vid = str(config['vlan_vid'])


class UserManager(object):
    """this class manages the v-r mapping of the tanents's network"""

    VLAN_TAG_TBL  = 0
    JMP_TBL = 1

    def __init__(self, *args, **kwargs):
        super(UserManager, self).__init__(*args, **kwargs)
        
        #dict{dpid=>dict{vlan=>list[list[end_ports], list[mid_ports]]}}
        self.vlan_to_port = {}
        self.port_to_vlan = {}   #dict{(dpid,port) => (vid, vdpid,vport)}
        self.vlan_to_sha1 = {}
        self.sha1_to_user = {}
        self.config = {}
        self.dpid_assign = {}    #dict{dpid=>{user:vdpid}}
        self.table_assign = {}   #dict{dpid=>{vlan_vid=>[beg, end, used]}}
        self.group_assign = {}   #dict{dpid=>{group_id=>(vid, vgroup_id)}}
        self.group_assign_r = {} #dict{dpid=>{(group, vtable_id)=>group_id}}

        self.load_config('../topology/config.json')
        self.get_vlan_ports_info()
        self.dpids = [id for id in self.vlan_to_port]
        self.init_users()

    def init_users(self):
        for x509, usr_conf in self.config.items():
            self.sha1_to_user[x509] = User(usr_conf, self)

    def set_group_assign(self, dpid, vid, group_id, vgroup_id):
        self.group_assign.setdefault(dpid, {})
        self.group_assign[dpid][group_id] = (vid, vgroup_id)

        self.group_assign_r.setdefault(dpid, {})
        self.group_assign_r[dpid][(vid, vgroup_id)] = group_id

    def assign_table(self, dpid, n_tables):
        """ partion the flow tables """
        if dpid not in self.vlan_to_port:
            self.table_assign.setdefault(dpid, {})
            self.table_assign[dpid].setdefault("others",
                                               [0, n_tables, 0])

            return

        n_vid = len(self.vlan_to_port[dpid])
        #we will divide the tables into n_vid+1 parts
        tbl_per_vid = n_tables // (n_vid+1)
        cnt = 0

        #assign tables to vids
        for vid in self.vlan_to_port[dpid]:
            self.table_assign.setdefault(dpid, {})
            self.table_assign[dpid].setdefault(vid, [0, 0, 0])
            self.table_assign[dpid][vid][0] = cnt * tbl_per_vid + self.JMP_TBL + 1
            self.table_assign[dpid][vid][1] = (cnt+1) * tbl_per_vid + self.JMP_TBL
            cnt = cnt + 1

        #the "others" routing table
        self.table_assign.setdefault(dpid, {})
        self.table_assign[dpid].setdefault("others",
                                           [cnt * tbl_per_vid + self.JMP_TBL + 1,
                                            (cnt+1) * tbl_per_vid + self.JMP_TBL,
                                            0])
        
    def load_config(self, filename):
        with open(filename) as f:
            self.config = json.load(f)
            
    def get_vlan_ports_info(self):
        for sha1, user_info in self.config.items():
            #ignore CM and the GOD
            if(user_info["type"] == "manager" or user_info["type"] == "god"):
                continue
            
            vid = str(user_info["vlan_vid"])
            self.vlan_to_sha1.setdefault(vid, sha1)

            #construct vlan_to_port and dpid_assign and port_to_vlan
            for vdpid, vsinfo in user_info["switches"].items():
                self.dpid_assign.setdefault(str(vsinfo["real"]), {})
                self.dpid_assign[str(vsinfo["real"])][str(vid)] = vdpid
                
                for rp, vp in vsinfo["rtov"].items():
                    self.vlan_to_port.setdefault(str(vsinfo["real"]), {})
                    self.vlan_to_port[str(vsinfo["real"])].setdefault(vid, [[],[]])
                    type = int(vsinfo["port_type"][rp])
                    self.vlan_to_port[str(vsinfo["real"])][vid][type].append(int(rp))
                    self.port_to_vlan[(int(vsinfo["real"]), int(rp))] = (int(vid), int(vdpid), int(vp))

    def get_user_by_cert(self, x509):
        digest = x509.digest('sha1')
        print(digest)
        return self.sha1_to_user.get(digest, None)
    
    def get_user(self, req, **kwargs):
        conn = req.environ.get('trustsdn_conn', None)
        x509 = conn.get_peer_certificate()
        if not x509:
            return None
        return self.get_user_by_cert(x509)
