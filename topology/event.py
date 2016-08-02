import logging
from ryu.controller.event import EventRequestBase
from ryu.topology.event import EventSwitchReply, EventLinkReply, EventHostReply


class EventSwitchRequest(EventRequestBase):
    def __init__(self, vdps=None, type="common"):
        super(EventSwitchRequest, self).__init__()
        self.dst = 'vswitches'
        self.vdps = vdps
        self.type = type

    def __str__(self):
        return 'EventSwitchRequest<src=%s, vdps=%s>' % \
            (self.src, self.vdps)


class EventLinkRequest(EventRequestBase):
    # If vdps is None, reply all list
    def __init__(self, vdps=None, dpid=None):
        super(EventLinkRequest, self).__init__()
        self.dst = 'vswitches'
        self.vdps = vdps
        self.dpid = dpid

    def __str__(self):
        return 'EventLinkRequest<src=%s, vdps=%s>' % \
            (self.src, self.vdps)


class EventHostRequest(EventRequestBase):
    # if vdps is None, replay all hosts
    def __init__(self, vdps=None, type="common"):
        super(EventHostRequest, self).__init__()
        self.dst = 'vswitches'
        self.vdps = vdps
        self.type = type

    def __str__(self):
        return 'EventHostRequest<src=%s, vdps=%s>' % \
            (self.src, self.vdps)
