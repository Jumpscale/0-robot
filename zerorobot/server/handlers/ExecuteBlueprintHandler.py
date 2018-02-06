# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json as JSON
import os

import jsonschema
from jsonschema import Draft4Validator

from flask import request
from js9 import j
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot import blueprint
from zerorobot.service_collection import ServiceConflictError
from zerorobot.template.base import BadActionArgumentError
from zerorobot.template_collection import (TemplateNameError,
                                           TemplateNotFoundError)
from zerorobot.template_uid import TemplateUID
from .views import task_view

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
        try:
            _instanciate_services(service)
        except TemplateNotFoundError:
            return JSON.dumps({'code': 404, 'message': "template '%s' not found" % service['template']}), 404, {"Content-type": 'application/json'}

    tasks_created = []
    for action_item in actions:
        try:
            tasks_created.extend(_schedule_action(action_item))
        except BadActionArgumentError as err:
            err_msg = "bad action argument for action %s: %s" % (action_item['action'], str(err))
            return JSON.dumps({'code': 400, 'message': err_msg}), 400, {"Content-type": 'application/json'}

    response = []
    for task, service in tasks_created:
        response.append(task_view(task, service))

    return JSON.dumps(response), 200, {"Content-type": 'application/json'}


def _instanciate_services(service_descr):
    try:
        srv = tcol.instantiate_service(service_descr['template'], service_descr['service'], service_descr.get('data', None))
    except ServiceConflictError as err:
        if err.service is None:
            raise j.exceptions.RuntimeError("should have the conflicting service in the exception")
        # err.service is the conflicting service, that's the one we want to update
        # with the new data from the blueprint
        err.service.data.update_secure(service_descr.get('data', {}))


def _schedule_action(action_item):
    template_uid = None
    template = action_item.get("template")
    if template:
        template_uid = TemplateUID.parse(template)

    service = action_item.get("service")
    action = action_item.get("action")
    args = action_item.get('args')
    if args and not isinstance(args, dict):
        raise TypeError("args should be a dict not %s" % type(args))

    candidates = []

    kwargs = {'name': service}
    if template_uid:
        kwargs.update({
            'template_host': template_uid.host,
            'template_account': template_uid.account,
            'template_repo': template_uid.repo,
            'template_name': template_uid.name,
            'template_version': template_uid.version,
        })
    # filter out None value
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    if len(kwargs) > 0:
        candidates = scol.find(**kwargs)
    else:
        candidates = scol.list_services()

    tasks = []
    for service in candidates:
        t = service.schedule_action(action, args=args)
        tasks.append((t, service))
    return tasks
