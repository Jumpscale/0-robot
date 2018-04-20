# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json

from flask import request

from zerorobot import service_collection as scol
from zerorobot.server.handlers.views import service_view

from zerorobot.server import auth


@auth.multi.login_required
def GetServiceHandler(service_guid):
    '''
    Get the detail of a service
    It is handler for GET /services/<service_guid>
    '''
    try:
        service = scol.get_by_guid(service_guid)
    except KeyError:
        return json.dumps({'code': 404, 'message': "service with guid '%s' not found" % service_guid}), \
            404, {"Content-type": 'application/json'}

    return json.dumps(service_view(service)), 200, {"Content-type": 'application/json'}
