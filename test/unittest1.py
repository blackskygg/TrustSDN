import unittest
import sys
import subprocess
import os.path
import logging
import cProfile



def setup_env():
    trustsdn_path = os.path.abspath(os.path.join(sys.path[0], '../..'))
    # add our project path to system path so that we can import our modules.
    sys.path.insert(1, trustsdn_path)

    # change current working path
    # make the private key file and certificate file can be found.
    os.chdir(sys.path[0])

    # enable debug
    from ryu import log
    log.early_init_log(logging.DEBUG)
    log.init_log()

def wsgi_app(appmgr):
    from trustsdn.server import wsgi
    private_key = './server_9E679BF3EDBF0689.key'
    cert_file = './server_9E679BF3EDBF0689.crt'
    wsgi = wsgi.start_service(appmgr, private_key, cert_file)
    return wsgi

def run_app():
    from ryu.lib import hub
    from ryu.base.app_manager import AppManager

    app_lists = ['trustsdn.topology.switches',
                 'trustsdn.server.user_manager',
                 'trustsdn.server.vlan_14',
                 'trustsdn.server.route_manager',
                 'trustsdn.server.ofctl_rest', # ofctl_rest
                 'trustsdn.server.gui_topology.gui_topology',
                 'trustsdn.server.topology'   # rest_topology
                ]


    app_mgr = AppManager.get_instance()
    app_mgr.load_apps(app_lists)

    # gui requires rest_topology and if use load_apps()
    # the rest_topology module will be loaded automaticlly
    # we dont want that happen
#    del app_mgr.applications_cls['ryu.app.rest_topology']

    contexts = app_mgr.create_contexts()
    services = []
    services.extend(app_mgr.instantiate_apps(**contexts))

    # start WSGI application
    thr = hub.spawn(wsgi_app(app_mgr))
    services.append(thr)
    try:
        hub.joinall(services)
    finally:
        app_mgr.close()

# DO Test
class TestServer(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestServer, self).__init__(*args, **kwargs)

    def test_main(self):
        run_app()

    def __del__(self):
        self.ryu.terminate()


if __name__ == '__main__':
    setup_env()
    unittest.main()





