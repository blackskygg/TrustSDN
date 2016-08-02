from trustsdn.topology import event


def get_switch(app, vdps, type = "common"):
    rep = app.send_request(event.EventSwitchRequest(vdps, type))
    return rep.switches

def get_link(app):
    rep = app.send_request(event.EventLinkRequest())
    return rep.links

def get_host(app, vdps, type = "common"):
    rep = app.send_request(event.EventHostRequest(vdps, type))
    return rep.hosts
