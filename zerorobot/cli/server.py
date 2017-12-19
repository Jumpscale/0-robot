
import click
from gevent import monkey
from zerorobot.robot import Robot

# need to patch sockets to make requests async
monkey.patch_all(
    socket=True,
    dns=True,
    time=True,
    select=True,
    thread=True,
    os=True,
    ssl=True,
    httplib=False,
    subprocess=False,
    sys=False,
    aggressive=True,
    Event=False,
    builtins=True,
    signal=True)


@click.group()
def server():
    pass


@server.command()
@click.option('--listen', '-L', help='listen address (default :6600)', default=':6600')
@click.option('--data-repo', '-D', required=True, help='URL of the git repository where to save the data of the zero robot')
@click.option('--template-repo', '-T', multiple=True, help='list of template repository URL')
@click.option('--robots', '-R', multiple=True, help='address of reachable robots')
def start(listen, data_repo, template_repo, robots):
    """
    start the 0-robot daemon.
    this will start the REST API on address and port specified by --listen and block
    """
    robot = Robot()

    for url in template_repo:
        robot.add_template_repo(url)

    for addr in robots:
        robot.add_remote_robot(addr)

    robot.set_data_repo(data_repo)
    robot.start(listen=listen)
