# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json
import os

import jsonschema
from flask import jsonify, request
from jsonschema import Draft4Validator

from zerorobot import service_collection as scol
from zerorobot.server.handlers.views import task_view
from zerorobot.template.base import ActionNotFoundError, BadActionArgumentError

from zerorobot.server import auth

dir_path = os.path.dirname(os.path.realpath(__file__))
TaskCreate_schema = json.load(open(dir_path + '/schema/TaskCreate_schema.json'))
TaskCreate_schema_resolver = jsonschema.RefResolver('file://' + dir_path + '/schema/', TaskCreate_schema)
TaskCreate_schema_validator = Draft4Validator(TaskCreate_schema, resolver=TaskCreate_schema_resolver)


@auth.service.login_required
def AddTaskToListHandler(service_guid):
    '''
    Add a task to the task list
    It is handler for POST /services/<service_guid>/task_list
    '''
    inputs = request.get_json()
    try:
        TaskCreate_schema_validator.validate(inputs)
    except jsonschema.ValidationError as e:
        return jsonify(code=400, message=str(e)), 400

    try:
        service = scol.get_by_guid(service_guid)
    except KeyError:
        return jsonify(code=404, message="service with guid '%s' not found" % service_guid), 404

    args = inputs.get('args', None)
    try:
        task = service.schedule_action(action=inputs['action_name'], args=args)
    except ActionNotFoundError:
        return jsonify(code=400, message="action '%s' not found" % inputs['action_name']), 400
    except BadActionArgumentError:
        return jsonify(code=400, message="the argument passed in the requests, doesn't match the signature of the action"), 400

    return jsonify(task_view(task, service)), 201
