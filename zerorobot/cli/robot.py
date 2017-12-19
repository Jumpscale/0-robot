import sys
from os import path
from pathlib import Path

import requests

import click
from js9 import j
from zerorobot.cli import utils


@click.group()
def robot():
    pass


@robot.command()
@click.argument('addr')
def connect(addr):
    """
    configure the zrobot CLI to work against the 0-robot pointed by --addr
    """
    if not utils.test_connection(addr):
        print("%s doesn't seems to be a valid 0-robot" % addr)
        sys.exit(1)

    j.data.serializer.yaml.dump(utils.cfg_file_path, {utils.cfg_key: addr})
    print("Connection to %s saved" % addr)


@robot.command()
def current():
    """
    print the address of the 0-robot configured
    """
    utils.get_addr()
