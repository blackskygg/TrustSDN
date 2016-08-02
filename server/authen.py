import json
from trustsdn.server.user_manager import User

class Authentication(object):
    def __init__(self, *args, **kwargs):
        self.config = self.load_config('../topology/config.json')

    def get_user_by_cert(self, x509):
        digest = x509.digest('sha1')
        print(digest)
        user_config = self.config.get(digest, None)
        user = None
        if user_config:
            user = User(user_config)
        return user

    def load_config(self, file):
        return json.load(open(file))

    def get_user(self, req, **kwargs):
        conn = req.environ.get('trustsdn_conn', None)
        x509 = conn.get_peer_certificate()
        if not x509:
            return None
        return self.get_user_by_cert(x509)
