# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

import json as JSON
import os

import jsonschema
from jsonschema import Draft4Validator

from flask import jsonify, request
from zerorobot import template_collection as tcol
from zerorobot.git import repo, url
from zerorobot.server import auth

dir_path = os.path.dirname(os.path.realpath(__file__))
TemplateRepository_schema = JSON.load(open(dir_path + '/schema/TemplateRepository_schema.json'))
TemplateRepository_schema_resolver = jsonschema.RefResolver(
    'file://' + dir_path + '/schema/', TemplateRepository_schema)
TemplateRepository_schema_validator = Draft4Validator(
    TemplateRepository_schema, resolver=TemplateRepository_schema_resolver)


@auth.admin.login_required
def CheckoutVersionTemplateRepoHandler():
    inputs = request.get_json()

    try:
        TemplateRepository_schema_validator.validate(inputs)
    except jsonschema.ValidationError as e:
        return jsonify(errors="bad request body"), 400

    tcol.checkout_repo(inputs.get('url'), inputs.get('branch'))

    return "", 204, {"Content-type": 'application/json'}
