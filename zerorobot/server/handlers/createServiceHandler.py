# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json
import os

import jsonschema
from flask import request, jsonify
from jsonschema import Draft4Validator

from zerorobot import template_collection as tcol
from zerorobot.server.handlers.views import service_view
from zerorobot.service_collection import ServiceConflictError
from zerorobot.template_collection import (TemplateConflictError,
                                           TemplateNotFoundError)

from zerorobot.server import auth


dir_path = os.path.dirname(os.path.realpath(__file__))
ServiceCreate_schema = json.load(open(dir_path + '/schema/ServiceCreate_schema.json'))
ServiceCreate_schema_resolver = jsonschema.RefResolver('file://' + dir_path + '/schema/', ServiceCreate_schema)
ServiceCreate_schema_validator = Draft4Validator(ServiceCreate_schema, resolver=ServiceCreate_schema_resolver)


@auth.admin.login_required
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
        return jsonify(code=400, message="bad request body"), 400

    try:
        TemplateClass = tcol.get(inputs['template'])
    except TemplateNotFoundError:
        return jsonify(code=404, message="template '%s' not found" % inputs['template']), 404
    except TemplateConflictError:
        return jsonify(code=4090, message="template with name '%s' is confusing, can't select template based only on its name, please use full UID" % inputs['template']), 409
    except ValueError as err:
        return jsonify(code=400, message=err.args[0]), 400

    try:
        service = tcol.instantiate_service(TemplateClass, inputs.get('name'), inputs.get('data', {}))
    except ServiceConflictError:
        service = None
        return jsonify(code=409, message="a service with name '%s' already exists" % inputs['name']), 409
    except Exception as err:
        service = None
        return jsonify(code=500, message=str(err)), 500

    output = service_view(service)
    try:
        output['secret'] = auth.user_jwt.create({'service_guid': service.guid})
    except auth.user_jwt.SigningKeyNotFoundError as err:
        return jsonify(code=500, message='error creating user secret: no signing key available'), 500
    except Exception as err:
        return jsonify(code=500, message='error creating user secret: %s' % str(err)), 500

    return jsonify(output), 201
