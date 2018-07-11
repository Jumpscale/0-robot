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
    if(is_god_token_valid(request.headers)):
        services = [service_view(s) for s in scol.find(**kwargs)]
    else:
        allowed_services = extract_guid_from_headers(request.headers)
        services = [service_view(s) for s in scol.find(**kwargs) if s.guid in allowed_services or scol.is_service_public(s.guid) is True]
    return json.dumps(services), 200, {"Content-type": 'application/json'}


def extract_guid_from_headers(headers):
    if 'ZrobotSecret' not in request.headers:
        return []

    services_guids = []
    ss = headers['ZrobotSecret'].split(' ')
    if len(ss) < 2:
        return []

    auth_type = ss[0]
    tokens = ss[1]
    if auth_type != 'Bearer' or not tokens:
        return []

    for token in tokens.split(' '):
        try:
            claims = auth.user_jwt.decode(token)
            guid = claims.get('service_guid')
            if guid:
                services_guids.append(guid)
        except:
            continue

    return services_guids

def is_god_token_valid(headers):
    
    if 'ZrobotSecret' not in request.headers:
        return False

    ss = headers['ZrobotSecret'].split(' ')
    #check if i have god token in header or not structrue ('Bearer', 'secret','Bearer','god_token')
    if len(ss) < 2:
        return False
    elif len(ss) == 2:
        god_token = ss[1]
    elif len(ss) == 4:
        god_token = ss[3]
    if config.god is True and auth.god_jwt.verify(god_token):
        return True
    return False