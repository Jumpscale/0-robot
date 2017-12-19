import sys

import click
from js9 import j
from zerorobot.cli import utils


def print_task(task, tb=False):
    state = task.state

    print("{created} - {guid} - {action} - {state}".format(
        created=j.data.time.epoch2HRDateTime(task.created),
        guid=task.guid,
        action=task.action_name,
        state=state))
    if tb and state == 'error':
        task.eco.printTraceback()


def sort_by_created(tasks):
    return sorted(tasks, key=lambda t: t.created)


@click.group()
def task():
    """
    group of command to manage task list of a service
    """
    pass


@task.command()
@click.argument('guid')
@click.argument('action')
# @click.option('data', help) TODO: find a way to pass data from CLI
def schedule(guid, action):
    """
    schedule an action on a service
    and prints the guid of the task created
    """
    if not guid:
        print("no service guid specified")
        sys.exit(1)

    if not action:
        print("no action specified")
        sys.exit(1)

    cl = utils.get_client()
    service = cl.services.guids[guid]
    task = service.schedule_action(action, args=None, resp_q=None)
    print('task created - %s' % task.guid)


@task.command()
@click.argument('guid')
@click.option('--all', help='also return task already executed tasks', default=False, is_flag=True)
def list(guid, all):
    """
    list all task of a service
    """
    if not guid:
        print("no service guid specified")
        sys.exit(1)

    cl = utils.get_client()
    service = cl.services.guids[guid]

    tasks = service.task_list.list_tasks(all=all)
    for task in sort_by_created(tasks):
        print("{created} - {guid} - {action} - {state}".format(
            created=j.data.time.epoch2HRDateTime(task.created),
            guid=task.guid,
            action=task.action_name,
            state=task.state))


@task.command()
@click.argument('guid', nargs=1)
@click.argument('task', nargs=1)
@click.option('--tb', help='print traceback in case state is error', default=False, required=False, is_flag=True)
def get(guid, task, tb):
    """
    print the detail of a task
    """
    if not guid:
        print("no service guid specified")
        sys.exit(1)

    if not task:
        print("no task guid specified")
        sys.exit(1)

    cl = utils.get_client()
    service = cl.services.guids[guid]
    try:
        task = service.task_list.get_task_by_guid(task)
    except KeyError:
        print("no task with guid %d" % task)
        sys.exit(1)

    print_task(task, tb)
