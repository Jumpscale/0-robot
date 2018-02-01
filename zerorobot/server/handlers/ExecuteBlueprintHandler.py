# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json as JSON
import os

import jsonschema
from jsonschema import Draft4Validator

from flask import request
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot import blueprint
from zerorobot.service_collection import ServiceConflictError

dir_path = os.path.dirname(os.path.realpath(__file__))
Blueprint_schema = JSON.load(open(dir_path + '/schema/Blueprint_schema.json'))
Blueprint_schema_resolver = jsonschema.RefResolver('file://' + dir_path + '/schema/', Blueprint_schema)
Blueprint_schema_validator = Draft4Validator(Blueprint_schema, resolver=Blueprint_schema_resolver)


def ExecuteBlueprintHandler():
    '''
    Execute a blueprint on the ZeroRobot
    It is handler for POST /blueprints
    '''
    inputs = request.get_json()
    try:
        Blueprint_schema_validator.validate(inputs)
    except jsonschema.ValidationError as err:
        return JSON.dumps({'code': 400, 'message': str(err)}), 400, {"Content-type": 'application/json'}

    try:
        actions, services = blueprint.parse(inputs['content'])
    except blueprint.BadBlueprintFormatError as err:
        return JSON.dumps({'code': 400, 'message': str(err.args[1])}), 400, {"Content-type": 'application/json'}

    for service in services:
        srv = None
        try:
            srv = tcol.instantiate_service(service['template'], service['service'], service['data'])
        except KeyError:
            return JSON.dumps({'code': 404, 'message': "template '%s' not found" % service['template']}), \
                404, {"Content-type": 'application/json'}
        except ServiceConflictError:
            srv = scol.get_by_name(service['service'])
            srv.data.update_secure(service.get('data', {}))

    for action_item in actions:
        schedule_action(action_item)

    return "", 204, {"Content-type": 'application/json'}


def schedule_action(action_item):
    template = action_item.get("template")
    service = action_item.get("service")
    action = action_item.get("action")
    candidates = []

    if template and service:
        candidates = scol.find(template_uid=template, name=service)
    elif template and not service:
        candidates = scol.find(template_uid=template)
    elif not template and service:
        candidates = scol.find(name=service)
    else:
        candidates = scol.list_services()

    for service in candidates:
        service.schedule_action(action)
