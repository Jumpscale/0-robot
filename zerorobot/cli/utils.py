
import sys
from os import path
from pathlib import Path

import requests

from jumpscale import j
from zerorobot.dsl.ZeroRobotManager import ZeroRobotManager

_JS_CONFIG_KEY = 'zrobot_current'


def test_connection(instance):
    cl = j.clients.zrobot.get(instance)
    addr = cl.config.data['url']
    try:
        _, resp = cl.api.services.listServices()
        return resp.status_code == 200, addr
    except requests.exceptions.ConnectionError:
        return False, addr


def get_instance():
    try:
        instance = j.core.state.stateGet(_JS_CONFIG_KEY)
    except j.exceptions.Input:
        print("No robot configured. Use 'zrobot robot connect' to configure one")
        sys.exit(1)

    if not instance:
        print("No robot configured. Use 'zrobot robot connect' to configure one")
        sys.exit(1)

    connected, addr = test_connection(instance)
    if not connected:
        print("A robot is configured at '%s', but it doesn't seems to be a valid 0-robot. Are you sure the 0-robot is up and running ?" % addr)
        sys.exit(1)

    return instance, addr


def get_client():
    instance, _ = get_instance()
    return ZeroRobotManager(instance)


def print_service(service):
    print("{template} - {guid} - {name}".format(
        guid=service.guid,
        name=service.name,
        template=service.template_uid
    ))
