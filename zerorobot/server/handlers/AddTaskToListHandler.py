# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json
import os

import jsonschema
from jsonschema import Draft4Validator

from flask import request
from zerorobot import service_collection as scol
from zerorobot.server.handlers.views import task_view
from zerorobot.template.base import ActionNotFoundError, BadActionArgumentError

dir_path = os.path.dirname(os.path.realpath(__file__))
TaskCreate_schema = json.load(open(dir_path + '/schema/TaskCreate_schema.json'))
TaskCreate_schema_resolver = jsonschema.RefResolver('file://' + dir_path + '/schema/', TaskCreate_schema)
TaskCreate_schema_validator = Draft4Validator(TaskCreate_schema, resolver=TaskCreate_schema_resolver)


def AddTaskToListHandler(service_guid):
    '''
    Add a task to the task list
    It is handler for POST /services/<service_guid>/task_list
    '''
    inputs = request.get_json()
    try:
        TaskCreate_schema_validator.validate(inputs)
    except jsonschema.ValidationError as e:
        print(e)
        return json.dumps({'code': 400, 'message': str(e)}), 400, {"Content-type": 'application/json'}

    try:
        service = scol.get_by_guid(service_guid)
    except KeyError:
        return json.dumps({'code': 404, 'message': "service with guid '%s' not found" % service_guid}), \
            404, {"Content-type": 'application/json'}

    args = inputs.get('args', None)
    try:
        task = service.schedule_action(action=inputs['action_name'], args=args)
    except ActionNotFoundError:
        return json.dumps({'code': 400, 'message': "action '%s' not found" % inputs['action_name']}), \
            400, {"Content-type": 'application/json'}
    except BadActionArgumentError:
        return json.dumps({'code': 400, 'message': "the argument passed in the requests, doesn't match the signature of the action"}), \
            400, {"Content-type": 'application/json'}

    return json.dumps(task_view(task, service)), 201, {"Content-type": 'application/json'}
