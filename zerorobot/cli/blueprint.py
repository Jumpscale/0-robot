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
        print("blueprint not found at %s" % blueprint)
        sys.exit(1)

    instance, _ = utils.get_instance()
    client = j.clients.zrobot.get(instance)

    content = j.data.serializer.yaml.load(blueprint)
    data = {'content': content}

    try:
        response, _ = client.api.blueprints.ExecuteBlueprint(data)

        # save secret of the service inside config manager
        for service in response.services:
            if service.secret not in client.config.data['secrets_']:
                secrets = client.config.data['secrets_']
                secrets.append(service.secret)
        # force re-creation of the connection with new secret added in the Authorization header
        client.config.save()
        client._api = None

        print("blueprint executed")
        print('list of services created:')
        print_services(response.services)
        print("list of tasks created:")
        print_tasks(response.tasks)
    except HTTPError as err:
        msg = err.response.json()['message']
        print("error during execution of the blueprint: %s" % msg)
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


def print_services(services):
    for service in services:
        print("{template} - {guid} - {name}".format(
            guid=service.guid,
            name=service.name,
            template=service.template
        ))
