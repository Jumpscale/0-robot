# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json

from zerorobot import template_collection as tcol
from zerorobot.server.handlers.views import template_view

from zerorobot.server import auth


@auth.admin.login_required
def ListTemplatesHandler():
    '''
    List all the templates available to the ZeroRobot
    It is handler for GET /templates
    '''
    templates = [template_view(t) for t in tcol.list_templates()]
    return json.dumps(templates), 200, {"Content-type": 'application/json'}
