import sys
from os import path
from pathlib import Path

import requests

from js9 import j

import click
from zerorobot.cli import utils

_location = 'j.clients.zrobot'


def _list():
    """
    list all instance of 0-robot register in the configmanager
    """
    return j.tools.configmanager.list(_location)


@click.group()
def robot():
    pass


@robot.command()
@click.argument('instance', required=True)
@click.argument('addr', required=False)
def connect(instance, addr):
    """
    configure the zrobot CLI to work against the 0-robot named --instance
    """
    # create new config
    if addr is not None:
        # create new configuration for this instance-addr
        cl = j.clients.zrobot.get(instance=instance, data={'url': addr})
        cl.config.data['url'] = addr
        cl.config.save()

    # just select existing robot
    if instance not in _list() and addr is None:
        print("instance '%s' not found. Use 'zrobot robot connect instance addr` to configure a new connection to a 0-robot" % instance)
        sys.exit(1)

    connected, addr = utils.test_connection(instance)
    if not connected:
        print("service running at %s doesn't seems to be a valid 0-robot" % addr)
        sys.exit(1)

    j.data.serializer.yaml.dump(utils.cfg_file_path, {utils.cfg_key: instance})
    print("Connection to %s saved" % instance)


@robot.command()
def list():
    """
    print all the instance of the 0-robot configured on the system
    """
    for instance in _list():
        cl = j.clients.zrobot.get(instance=instance)
        print('%s @ %s' % (instance, cl.config.data['url']))


@robot.command()
def current():
    """
    print the address of the 0-robot configured
    """
    instance, addr = utils.get_instance()
    print('%s @ %s' % (instance, addr))
