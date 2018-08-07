import sys

import click
from requests.exceptions import HTTPError

from jumpscale import j
from zerorobot.cli import utils
from zerorobot import config
from zerorobot.server import auth


@click.group()
def godtoken():
    """
    Get god token of the instance
    """
    pass


@godtoken.command()
def get():
    print("god token: %s " % auth.god_jwt.create())
