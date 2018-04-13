# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json
import os

import jsonschema
from jsonschema import Draft4Validator

from flask import request
from zerorobot import template_collection as tcol
from zerorobot.server.handlers.views import service_view
from zerorobot.service_collection import ServiceConflictError
from zerorobot.template_collection import TemplateNotFoundError, TemplateConflictError

dir_path = os.path.dirname(os.path.realpath(__file__))
ServiceCreate_schema = json.load(open(dir_path + '/schema/ServiceCreate_schema.json'))
ServiceCreate_schema_resolver = jsonschema.RefResolver('file://' + dir_path + '/schema/', ServiceCreate_schema)
ServiceCreate_schema_validator = Draft4Validator(ServiceCreate_schema, resolver=ServiceCreate_schema_resolver)


def createServiceHandler():
    '''
    create a new service
    It is handler for POST /services
    '''
    inputs = request.get_json()
    try:
        ServiceCreate_schema_validator.validate(inputs)
    except jsonschema.ValidationError as e:
        print(e)
        return json.dumps({'code': 400, 'message': "bad request body"}), 400, {"Content-type": 'application/json'}

    try:
        TemplateClass = tcol.get(inputs['template'])
    except TemplateNotFoundError:
        return json.dumps({'code': 404, 'message': "template '%s' not found" % inputs['template']}), \
            404, {"Content-type": 'application/json'}
    except TemplateConflictError:
        return json.dumps({'code': 4090, 'message': "template with name '%s' is confusing, can't select template based only on its name, please use full UID" % inputs['template']}), \
            409, {"Content-type": 'application/json'}
    except ValueError as err:
        return json.dumps({'code': 400, 'message': err.args[0]}), 400, {"Content-type": 'application/json'}

    try:
        service = tcol.instantiate_service(TemplateClass, inputs.get('name'), inputs.get('data', {}))
    except ServiceConflictError:
        service = None
        return json.dumps({'code': 409, 'message': "a service with name '%s' already exists" % inputs['name']}), \
            409, {"Content-type": 'application/json'}
    except Exception as err:
        service = None
        return json.dumps({'code': 500, 'message': str(err)}), 500, {"Content-type": 'application/json'}

    return json.dumps(service_view(service)), 201, {"Content-type": 'application/json'}
