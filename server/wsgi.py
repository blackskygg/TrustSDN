import logging
from eventlet import wsgi
from eventlet.green import socket
from eventlet.green.OpenSSL import SSL, crypto

import pdb


class LoggerWraper(object):
    def __init__(self):
        self.log = logging.getLogger('trustsdn.wsgi')
    def write(self, message):
        self.log.info(message.rstrip('\n'))


# customize RequestHandler to inject session layer data to environ
class TrustSdnRequestHandler(wsgi.HttpProtocol):
    def get_environ(self):
        env = wsgi.HttpProtocol.get_environ(self)
        env['trustsdn_conn'] = self.connection
        return env

class WSGIServer(object):
    def __init__(self, listen_info, handle=None,
                 ssl=True, private_key='', cert_file='', **kwargs):
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if ssl and private_key and cert_file:
            context = SSL.Context(SSL.SSLv23_METHOD)
            context.use_privatekey_file(private_key)
            context.use_certificate_file(cert_file)
            context.load_verify_locations(None, '/etc/ssl/certs/')

            context.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT
                               |SSL.VERIFY_CLIENT_ONCE, lambda *x: True)
            self.conn = SSL.Connection(context, server)
            # configure as server
            # self.conn.set_accept_state()
        else:
            self.conn = server

        self.conn.bind(listen_info)
        self.conn.listen(50)
        self.handle = handle

    def serve_forever(self):
        self.logger = LoggerWraper()
        wsgi.server(self.conn, self.handle, self.logger,
                             protocol=TrustSdnRequestHandler)

    def __call__(self):
        self.serve_forever()

def start_service(app_mgr, private_key, cert_file):
    from ryu.app.wsgi import WSGIApplication
    for instance in app_mgr.contexts.values():
        if instance.__class__ == WSGIApplication:
            server = WSGIServer(('', 8080), instance,
                                True, private_key, cert_file)
            return server

    return None
