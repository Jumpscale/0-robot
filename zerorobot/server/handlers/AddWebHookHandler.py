# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify, request

import json as JSON
import jsonschema
from jsonschema import Draft4Validator

import os

from zerorobot import config

dir_path = os.path.dirname(os.path.realpath(__file__))
WebHook_schema = JSON.load(open(dir_path + '/schema/WebHook_schema.json'))
WebHook_schema_resolver = jsonschema.RefResolver('file://' + dir_path + '/schema/', WebHook_schema)
WebHook_schema_validator = Draft4Validator(WebHook_schema, resolver=WebHook_schema_resolver)


def AddWebHookHandler():

    inputs = request.get_json()

    try:
        WebHook_schema_validator.validate(inputs)
    except jsonschema.ValidationError as e:
        return jsonify(code=400, message="bad request body"), 400

    webhooks = config.webhooks
    webhook = webhooks.add(inputs['url'], inputs['kind'])

    return jsonify(webhook.as_dict()), 201
