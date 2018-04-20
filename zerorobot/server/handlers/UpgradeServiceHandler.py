# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json
import os

import gevent
import jsonschema
from flask import jsonify, request
from jsonschema import Draft4Validator

import zerorobot.service_collection as scol
import zerorobot.template_collection as tcol
from zerorobot.server.handlers.views import service_view
from zerorobot.template_uid import TemplateUID

from zerorobot.server import auth

dir_path = os.path.dirname(os.path.realpath(__file__))
ServiceUpgradeRequest_schema = json.load(open(dir_path + '/schema/ServiceUpgradeRequest_schema.json'))
ServiceUpgradeRequest_schema_resolver = jsonschema.RefResolver(
    'file://' + dir_path + '/schema/', ServiceUpgradeRequest_schema)
ServiceUpgradeRequest_schema_validator = Draft4Validator(
    ServiceUpgradeRequest_schema,
    resolver=ServiceUpgradeRequest_schema_resolver)


@auth.admin.login_required
def UpgradeServiceHandler(service_guid):

    inputs = request.get_json()

    try:
        ServiceUpgradeRequest_schema_validator.validate(inputs)
    except jsonschema.ValidationError as e:
        return json.dumps({'code': 400, 'message': "bad request body"}), 400, {"Content-type": 'application/json'}

    try:
        service = scol.get_by_guid(service_guid)
    except KeyError:
        return json.dumps({'code': 404, 'message': "service with guid '%s' not found" % service_guid}), \
            404, {"Content-type": 'application/json'}

    try:
        new_template_uid = TemplateUID.parse(inputs['template'])
        new_template = tcol.get(new_template_uid)
        service = scol.upgrade(service, new_template)
    except KeyError:
        return json.dumps({'code': 404, 'message': "template '%s' not found" % str(new_template_uid)}), \
            404, {"Content-type": 'application/json'}

    return json.dumps(service_view(service)), 200, {"Content-type": 'application/json'}
