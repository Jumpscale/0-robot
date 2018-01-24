"""
This module holds all the logic regarding parsing and processing of a blueprint.

It is being used from the REST API server handlers
"""


import re

import yaml

from js9 import j
from zerorobot.template_uid import TemplateUID


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
        keys = ['template', 'service', 'recurring', 'force']
        for action in actions:
            item = {'action': action}
            for k in keys:
                if k == 'force':
                    item[k] = bool(block.get(k, False))
                else:
                    item[k] = block.get(k, '')
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
    # if ":" in name:
    #     raise BadBlueprintFormatError("service names (%s) cannot contain colons (:)" % name)
    # if ":" in template:
    #     raise BadBlueprintFormatError("template names (%s) cannot contain colons (:)" % template)

    # TODO: re-enabled when template alias is implemented
    # if template.find(".") != -1:
    #     rolefound, _ = template.split(".", 1)
    # else:
    #     rolefound = template
    # if role != "" and role != rolefound:
    #     self.logger.info(
    #         "ignore load from blueprint based on role for: %s:%s" % (template, name))
    #     continue

    # check if we can find template and if not then check if there is a blueprint.  name...
    # if not self.aysrepo.templateExists(template) and not template.startswith('blueprint.'):
    #     blueaysname = 'blueprint.%s' % template
    #     if self.aysrepo.templateExists(blueaysname):
    #         template = blueaysname

    # if not self.aysrepo.templateExists(template):
    #     raise j.exceptions.Input(message="Cannot find actor:%s" %
    #                              template, level=1, source="", tags="", msgpub="")
    # actor = self.aysrepo.actorGet(template, context=context)
    # args = {} if item is None else item
    # await actor.asyncServiceCreate(instance=name, args=args, context=context)

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
    try:
        TemplateUID.parse(uid)
    except ValueError:
        raise BadBlueprintFormatError("Template uid not valid")
    return True


class BadBlueprintFormatError(Exception):

    def __init__(self, message, block=None):
        super().__init__(self, message)
        self.block = block
