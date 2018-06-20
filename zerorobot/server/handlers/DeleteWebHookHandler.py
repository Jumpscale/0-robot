# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify, request
from zerorobot import config


def DeleteWebHookHandler(id):

    webhooks = config.webhooks
    webhooks.delete(id)

    return '', 204
