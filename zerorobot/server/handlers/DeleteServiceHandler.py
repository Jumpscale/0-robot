# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from zerorobot import service_collection as scol


def DeleteServiceHandler(service_guid):
    '''
    Delete a service
    It is handler for DELETE /services/<service_guid>
    '''

    try:
        service = scol.get_by_guid(service_guid)
        service.delete()
    except KeyError:
        pass

    return "", 204, {"Content-type": 'application/json'}
