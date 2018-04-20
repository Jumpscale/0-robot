# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json

from flask import request

from zerorobot import service_collection as scol
from zerorobot.server.handlers.views import service_view
from zerorobot.server import auth


@auth.admin.login_required
def listServicesHandler():
    '''
    List all the services known by the ZeroRobot.
    It is handler for GET /services
    '''
    kwargs = {}
    for x in ["name", "template_uid", "template_host", "template_account", "template_repo", "template_name", "template_version"]:
        val = request.args.get(x)
        if val:
            kwargs[x] = val

    services = [service_view(s) for s in scol.find(**kwargs)]
    return json.dumps(services), 200, {"Content-type": 'application/json'}
