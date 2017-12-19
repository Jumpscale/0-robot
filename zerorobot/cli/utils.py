
import sys
from os import path
from pathlib import Path

import requests

from js9 import j
from zerorobot.dsl.ZeroRobotClient import ZeroRobotClient

cfg_file_path = path.join(str(Path.home()), '.zrobot.yml')
cfg_key = 'address_robot'


def test_connection(addr):
    try:
        resp = requests.head(addr)
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def get_addr():
    if not path.exists(cfg_file_path):
        print("No robot configured. Use 'zrobot robot connect' to configure one")
        sys.exit(1)

    cfg = j.data.serializer.yaml.load(cfg_file_path)
    addr = cfg.get(cfg_key)
    if not addr:
        print("No robot configured. Use 'zrobot robot connect' to configure one")
        sys.exit(1)

    if not test_connection(addr):
        print("A robot is configured at '%s', but it doesn't seems to be a valid 0-robot. Are you sure the 0-robot is up and running ?" % addr)
        sys.exit(1)

    return addr


def get_client():
    addr = get_addr()
    return ZeroRobotClient(addr)


def print_service(service):
    print("{template} - {guid} - {name}".format(
        guid=service.guid,
        name=service.name,
        template=service.template_uid
    ))
