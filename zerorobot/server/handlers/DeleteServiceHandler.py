# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.
from flask import jsonify, request

from zerorobot import service_collection as scol
from zerorobot.server import auth


@auth.multi.login_required
def DeleteServiceHandler(service_guid):
    '''
    Delete a service
    It is handler for DELETE /services/<service_guid>
    '''

    try:
        service = scol.get_by_guid(service_guid)
        service.delete()
    except scol.ServiceNotFoundError:
        pass

    return "", 204, {"Content-type": 'application/json'}
