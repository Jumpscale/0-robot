# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify
from zerorobot import config


def GetRobotInfoHandler():

    output = {
        'repositories': {
            'data': {
                'url': config.data_repo.url or "",
            },
            'config': {
                'url': config.config_repo.url or "",
            }
        },
    }
    if config.data_repo.last_pushed:
        output['repositories']['data']['last_pushed'] = config.data_repo.last_pushed
    if config.config_repo.last_pushed:
        output['repositories']['config']['last_pushed'] = config.config_repo.last_pushed
    if config.mode:
        output['type'] = config.mode

    return jsonify(output)
