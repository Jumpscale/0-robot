import sys

import click
from zerorobot.cli import utils
from zerorobot.dsl.ZeroRobotClient import ZeroRobotClient


def sorted_by_uid(templates):
    return sorted(templates, key=lambda t: t.uid)


@click.group()
def template():
    pass


@template.command()
@click.argument('addr')
def add(addr):
    """
    add a template repository to the robot
    """
    if not addr:
        print('not repository address specified')
        sys.exit(1)

    cl = utils.get_client()
    templates = cl.templates.add_repo(addr)
    print("template added:")
    for template in sorted_by_uid(templates):
        print(template.uid)


@template.command()
def list():
    """
    list all templates
    """
    cl = utils.get_client()
    for template in sorted_by_uid(cl.templates.uids.values()):
        print(template.uid)
