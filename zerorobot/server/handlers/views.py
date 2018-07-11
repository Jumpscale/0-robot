from zerorobot import service_collection as scol
from flask import request
from zerorobot import config
from zerorobot.server import auth
import json


def service_view(service):
    s = {
        "template": str(service.template_uid),
        "version": service.version,
        "name": service.name,
        "guid": service.guid,
        "state": state_view(service.state),
        "actions": [],
        "public": scol.is_service_public(service.guid)
    }
    if config.god:
        s['data'] = service.data
    return s


def state_view(state):
    out = []
    for category, tags in state.categories.items():
        for tag, state in tags.items():
            out.append({
                'category': category,
                'tag': tag,
                'state': state,
            })
    return out


def task_view(task, service):
    eco = None
    result = None

    if task.eco is not None:
        eco = json.loads(task.eco.json)
    if task.result is not None:
        result = json.dumps(task.result)

    return {
        'template_name': service.template_name,
        'service_name': service.name,
        'service_guid': service.guid,
        'action_name': task.action_name,
        'state': task.state,
        'guid': task.guid,
        'created': task.created,
        'duration': task.duration,
        'eco': eco,
        'result': result
    }


def template_view(template):
    return {
        "uid": str(template.template_uid),
        "host": template.template_uid.host,
        "account": template.template_uid.account,
        "repository": template.template_uid.repo,
        "name": template.template_uid.name,
        "version": template.template_uid.version,
    }