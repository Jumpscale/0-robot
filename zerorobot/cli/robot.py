import sys

import click

from jumpscale import j
from zerorobot.cli import utils


def _list():
    """
    list all instance of 0-robot register in the configmanager
    """
    return j.clients.zrobot.list()


@click.group()
def robot():
    pass


@robot.command()
@click.argument('instance', required=True)
@click.argument('addr', required=False)
@click.argument('jwt', required=False)
def connect(instance, addr, jwt):
    """
    configure the zrobot CLI to work against the 0-robot

    examples:

    - create a new connection: `zrobot robot connect myRobot http://myrobot.com:6600`

    - create a new connection to a JWT protected robot: `zrobot robot connect myRobot http://myrobot.com:6600 eyJhbGciOiJFUzM4NCIsInR5cCI6IkpXVCJ9.eyJh......`

    - connect to an already configured robot: `zrobot robot connect myRobot`
    """
    # create new config
    if addr is not None:
        # create new configuration for this instance-addr
        data = {'url': addr}
        if jwt:
            data['jwt_'] = jwt
        # make sure instance is clean
        j.clients.zrobot.delete(instance)
        cl = j.clients.zrobot.get(instance=instance, data=data, create=True, interactive=False, die=True)
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

    j.core.state.stateSet(utils._JS_CONFIG_KEY, instance, save=True)
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


@robot.command()
@click.argument('instance', required=True)
def delete(instance):
    """
    delete a instance of the 0-robot configuration
    """
    # just select existing robot
    if instance not in _list():
        return
    j.clients.zrobot.delete(instance)
