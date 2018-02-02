import sys

import click
from requests.exceptions import HTTPError

from js9 import j
from zerorobot.cli import utils


@click.group()
def blueprint():
    """
    Group of command to execute blueprint on 0-robot
    """
    pass


@blueprint.command()
@click.argument("blueprint")
def execute(blueprint):
    if not j.sal.fs.exists(blueprint):
        print("blueprint %s doesn't not found")
        sys.exit(1)

    instance, _ = utils.get_instance()
    client = j.clients.zrobot.get(instance)

    content = j.data.serializer.yaml.load(blueprint)
    data = {'content': content}

    try:
        tasks, _ = client.api.blueprints.ExecuteBlueprint(data)
        print("blueprint executed")
        print("list of taks created with this blueprint:")
        print_tasks(tasks)
    except HTTPError as err:
        msg = err.response.json()['message']
        print(msg)
        return sys.exit(1)


def print_tasks(tasks):
    to_print = []
    for task in tasks:
        to_print.append({
            'template': task.template_name,
            'name': task.service_name,
            'action': task.action_name,
            'task uid': task.guid,
        })
    print(j.data.serializer.yaml.dumps(to_print))
