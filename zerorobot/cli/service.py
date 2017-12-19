import sys

import click
from zerorobot.cli import utils
from zerorobot.cli.task import task
from zerorobot.dsl.ZeroRobotClient import ZeroRobotClient
from zerorobot.service_collection import ServiceConflictError


def _sort_by_template(services):
    return sorted(services, key=lambda x: x.template_uid)


def print_service(service):
    print("{template} - {guid} - {name}".format(
        guid=service.guid,
        name=service.name,
        template=service.template_uid
    ))


@click.group()
def service():
    """
    group of command to manage services
    """
    pass


@service.command()
@click.option('--template', '-t', help='template UID', required=True)
@click.option('--name', '-n', help='service name', required=True)
@click.option('--data', '-d', help='service schema data', required=False, default=None)
def create(template, name, data=None):
    """
    create a new service
    """
    cl = utils.get_client()
    try:
        service = cl.services.create(template, name, data)
    except ServiceConflictError as err:
        print(str(err))
        sys.exit(1)

    print("service created")
    print_service(service)


@service.command()
def list():
    """
    list all the services
    """
    cl = utils.get_client()
    services = cl.services.names.values()

    for s in _sort_by_template(services):
        print_service(s)


@service.command()
@click.argument('guid')
def delete(guid):
    """
    delete a service
    """
    if not guid:
        print("not guid specified")
        sys.exit(1)

    cl = utils.get_client()
    try:
        service = cl.services.guids[guid]
        service.delete()
    except KeyError:
        return
