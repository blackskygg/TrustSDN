# Copyright (C) 2014 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Usage example

1. Join switches (use your favorite method):
$ sudo mn --controller remote --topo tree,depth=3

2. Run this application:
$ PYTHONPATH=. ./bin/ryu run \
    --observe-links ryu/app/gui_topology/gui_topology.py

3. Access http://<ip address of ryu host>:8080 with your web browser.
"""

import os

from webob.static import DirectoryApp

from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from trustsdn.server.user_manager import UserManager


PATH = os.path.dirname(__file__)


# Serving static files
class GUIServerApp(app_manager.RyuApp):
    _CONTEXTS = {
        'wsgi': WSGIApplication,
        'user_manager': UserManager
    }

    def __init__(self, *args, **kwargs):
        super(GUIServerApp, self).__init__(*args, **kwargs)

        wsgi = kwargs['wsgi']
        auth = kwargs['user_manager']

        self.data = {'auth' : auth}
        wsgi.register(GUIServerController, self.data)


class GUIServerController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(GUIServerController, self).__init__(req, link, data, **config)
        self.auth = data['auth']
        path = "%s/html/" % PATH
        self.static_app = DirectoryApp(path)

    @route('gui', '/gui/{filename:.*}')
    def static_handler(self, req, **kwargs):
        user = self.auth.get_user(req, **kwargs)
        type = user.user_type

        filename = kwargs['filename']
        if filename == 'topology':
            if type == "god":
                req.path_info = "index_god.html"
            elif type == "manager":
                req.path_info = "index_manager.html"
            else:
                req.path_info = "index.html"
        else:
            req.path_info = filename

        return self.static_app(req)


app_manager.require_app('trustsdn.server.topology')
app_manager.require_app('ryu.app.ws_topology')
app_manager.require_app('trustsdn.server.ofctl_rest')
