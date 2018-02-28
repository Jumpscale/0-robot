
from gevent import monkey

# need to patch sockets to make requests async
monkey.patch_all(subprocess=False)

from js9 import j
import click
from zerorobot.robot import Robot


@click.group()
def server():
    pass


@server.command()
@click.option('--listen', '-L', help='listen address (default :6600)', default=':6600')
@click.option('--data-repo', '-D', required=True, help='URL of the git repository where to save the data of the zero robot')
@click.option('--template-repo', '-T', multiple=True, help='list of template repository URL')
@click.option('--config-repo', '-C', required=False, help='URL of the configuration repository (https://github.com/Jumpscale/core9/blob/development/docs/config/configmanager.md)')
@click.option('--debug', help='enable debug logging', is_flag=True, default=False)
def start(listen, data_repo, template_repo, config_repo, debug):
    """
    start the 0-robot daemon.
    this will start the REST API on address and port specified by --listen and block
    """
    level = "INFO"
    if debug:
        level = "DEBUG"

    j.logger.handlers_level_set(level)
    j.logger.loggers_level_set(level)

    robot = Robot()

    for url in template_repo:
        robot.add_template_repo(url)

    robot.set_data_repo(data_repo)
    if config_repo:
        robot.set_config_repo(config_repo)

    robot.start(listen=listen)
