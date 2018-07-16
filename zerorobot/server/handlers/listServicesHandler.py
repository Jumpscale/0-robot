# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json

from flask import request

from zerorobot import service_collection as scol
from zerorobot.server.handlers.views import service_view
from zerorobot.server import auth
from zerorobot import config


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

    if auth.god_jwt.check_god_token(request):
        # god token passed, we list all the services
        services = [service_view(s) for s in scol.find(**kwargs)]
    else:
        # normal flow, only return service for which the user has the secret
        allowed_services = auth.user_jwt.extract_service_guid(request)
        services = [service_view(s) for s in scol.find(**kwargs) if s.guid in allowed_services or scol.is_service_public(s.guid) is True]

    return json.dumps(services), 200, {"Content-type": 'application/json'}
