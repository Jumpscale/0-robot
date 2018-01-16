# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json
import os

import jsonschema
from jsonschema import Draft4Validator

from flask import request
from zerorobot import template_collection as tcol
from zerorobot.server.handlers.views import template_view
from zerorobot.service_collection import ServiceConflictError

dir_path = os.path.dirname(os.path.realpath(__file__))
TemplateRepository_schema = json.load(open(dir_path + '/schema/TemplateRepository_schema.json'))
TemplateRepository_schema_resolver = jsonschema.RefResolver(
    'file://' + dir_path + '/schema/', TemplateRepository_schema)
TemplateRepository_schema_validator = Draft4Validator(
    TemplateRepository_schema, resolver=TemplateRepository_schema_resolver)


def AddTemplateRepoHandler():
    '''
    Clone a template repository and make the templates available to the ZeroRobot
    It is handler for POST /templates
    '''
    inputs = request.get_json()
    try:
        TemplateRepository_schema_validator.validate(inputs)
    except jsonschema.ValidationError as e:
        return json.dumps({'code': 400, 'message': "bad request body"}), 400, {"Content-type": 'application/json'}

    # TODO: handle branches
    added = tcol.add_repo(inputs['url'])
    templates = [template_view(t) for t in added]
    return json.dumps(templates), 201, {"Content-type": 'application/json'}
