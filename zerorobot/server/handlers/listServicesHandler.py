# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json

from zerorobot import service_collection as scol
from zerorobot.server.handlers.views import service_view


def listServicesHandler():
    '''
    List all the services known by the ZeroRobot.
    It is handler for GET /services
    '''
    services = [service_view(s) for s in scol.list_services()]
    return json.dumps(services), 200, {"Content-type": 'application/json'}
