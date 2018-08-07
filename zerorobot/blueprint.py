"""
This module holds all the logic regarding parsing and processing of a blueprint.

It is being used from the REST API server handlers
"""


import re

import yaml

from jumpscale import j
from zerorobot.template_uid import TemplateUID
from zerorobot import template_collection as tcol


def parse(content):
    """
    Parse a bluprint object and extract 3 types of blocks

    action block: list of actions required to be executed on which service
    e.g:

    ```python
    [{
        'template': 'node',
        'name': 'node1',
        'recurring': 1m,
        'action': 'start'
        'args': {
            'foo':'bar'
        }
    }]
    ```
    service block: create/update of a service with its data
    e.g.:

    ```
    [{
        'template': 'node',
        'service': 'node',
        'data': {'foo': 'bar'}
    }]
    ```
    return a tuple containing these blocks: (actions, services)
    """
    if isinstance(content, str):
        content = j.data.serializer.yaml.ordered_load(content, yaml.SafeLoader) or {}

    actions = []
    services = []
    # event_filters = []
    for key, block in content.items():
        if key == 'actions':
            actions.extend(_parse_actions(block))
        # TODO: not sure we still want to support that
        # elif key == 'eventFilters':
        #     event_filters.append(_parse_event_filter(block))
        elif key == 'services':
            for service_info in block:
                for name, data in service_info.items():
                    services.append(_parse_service(name, data))
    return (actions, services)


def _parse_actions(action_blocks):
    if not isinstance(action_blocks, list):
        action_blocks = [action_blocks]

    result = []
    for block in action_blocks:
        if "actions" not in block:
            raise BadBlueprintFormatError("need to specify action key in action block", {'actions': dict(block)})

        actions = block["actions"]

        if not isinstance(actions, list):
            actions = [actions]

        actions = [item.strip() for item in actions]
        keys = ['template', 'service', 'recurring', 'args']
        for action in actions:
            item = {'action': action}
            for k in keys:
                if k in block:
                    item[k] = block[k]
            result.append(item)

    return result


def _parse_event_filter(block):
    result = {}
    keys = ['template', 'service', 'channel', 'command', 'secret', 'actions']
    for k in keys:
        result[k] = block.get(k, '')
    return result


def _parse_service(key, data):
    # for key, item in model.items():
    if key.find("__") == -1:
        raise BadBlueprintFormatError("Key for service creation is not right format, needs to be '$template__$instance', found:'%s'" % key)

    template, name = key.split("__", 1)
    # TODO: move this into name_validation function
    validate_service_name(name)
    validate_template_uid(template)

    return {
        'template': template,
        'service': name,
        'data': data
    }


def validate_service_name(name):
    """
    Validates that service have valid name
    """
    if not re.sub("[-_.]", "", name).isalnum():
        message = "Service name should be digits or alphanumeric. you passed [%s]" % name
        raise BadBlueprintFormatError(message)
    return True


def validate_template_uid(uid):
    """
    Validates that template have valid name
    """
    # now that we can reference template just with the name,
    # just return true here, and more validation will happens
    # later when instantiating services
    return True


class BadBlueprintFormatError(Exception):

    def __init__(self, message, block=None):
        super().__init__(self, message)
        self.block = block
