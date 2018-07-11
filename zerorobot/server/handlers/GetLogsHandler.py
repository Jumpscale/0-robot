# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import os
from flask import request
from flask import jsonify, request, Response
from js9 import j
from zerorobot import service_collection as scol
from zerorobot import config
from zerorobot.server import auth


@auth.service.login_required
def GetLogsHandler(service_guid):
    
    if is_god_token_valid(request.headers) is False:
        return jsonify(code=400, message="god mode is not enable on the 0-robot, logs are not accessible"), 400

    try:
        service = scol.get_by_guid(service_guid)
    except KeyError:
        return jsonify(code=404, message="service with guid '%s' not found" % service_guid), 404

    log_file = os.path.join(j.dirs.LOGDIR, 'zrobot', service.guid)
    if not os.path.exists(log_file):
        return jsonify(logs=''), 200

    with open(log_file) as f:
        return jsonify(logs=f.read()), 200

def is_god_token_valid(headers):
    
    if 'ZrobotSecret' not in request.headers:
        return False

    ss = headers['ZrobotSecret'].split(' ')
    #check if i have god token in header or not structrue ('Bearer', 'secret','god_token')
    if len(ss) < 2:
        return False
    elif len(ss) == 2:
        god_token = ss[1]
    else:
        god_token = ss[2]
    if config.god is True and auth.god_jwt.verify(god_token):
        return True
    return False