# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json

from zerorobot import service_collection as scol


def ListActionsHandler(service_guid):
    '''
    List all the possible action a service can do.
    It is handler for GET /services/<service_guid>/actions
    '''

    try:
        service = scol.get_by_guid(service_guid)
    except KeyError:
        return json.dumps({'code': 404, 'message': "service with guid '%s' not found" % service_guid}), \
            404, {"Content-type": 'application/json'}

    actions = get_actions_list(service)

    return json.dumps(actions), 200, {"Content-type": 'application/json'}


def get_actions_list(obj):
    """
    extract the method name that the service has that are not the
    method comming from the template base
    """
    skip = ['load', 'save', 'schedule_action', 'recurring_action']
    actions = []
    for name in dir(obj):
        if name in skip or name.startswith('_'):
            continue
        if callable(getattr(obj, name)):
            actions.append({'name': name})
    return actions
