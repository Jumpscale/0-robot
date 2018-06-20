# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify, request
from zerorobot.robot import config


def GetRobotInfoHandler():

    output = {
        'repositories': {
            'data': {
                'url': config.data_repo.url,
                'last_pushed': config.data_repo.last_pushed,
            },
            'config': {
                'url': config.config_repo.url,
                'last_pushed': config.config_repo.last_pushed,
            }
        },
        'type': config.mode
    }
    return jsonify(output)
