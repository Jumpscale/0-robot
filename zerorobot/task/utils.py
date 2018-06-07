from js9 import j

from . import (PRIORITY_NORMAL, PRIORITY_RECURRING, PRIORITY_SYSTEM,
               TASK_STATE_ERROR, TASK_STATE_NEW, TASK_STATE_OK,
               TASK_STATE_RUNNING)
from .task import Task


def _instantiate_task(task, service):
    func = getattr(service, task['action_name'])
    t = Task(func, task['args'])
    if task['state'] in [TASK_STATE_RUNNING, TASK_STATE_NEW]:
        t.state = TASK_STATE_NEW
    else:
        t.state = task['state']
    t.guid = task['guid']
    if task['eco']:
        t._eco = j.core.errorhandler.getErrorConditionObject(ddict=task['eco'])
    t._result = task.get('result')
    t._created = task.get('created')
    t._duration = task.get('duration')
    return t


def wait_all(tasks, timeout=60, die=False):
    """
    helper method to wait for a list of tasks

    :param tasks: iterable that contains zerorobot.task.Task objects
    :type tasks: iterable
    :param timeout: timeout per task, defaults to 60
    :param timeout: int, optional
    :param die: if True, raise any exception that was raise in the tasks, defaults to False
    :param die: bool, optional
    :raises TypeError: raised if the iterable does not contains only zerorobot.task.Task
    :return: a list of all the result from the tasks
    :rtype: list
    """
    results = []
    for task in iter(tasks):
        if not isinstance(task, Task):
            raise TypeError("element of tasks should be an instance of zerorobot.task.Task")
        try:
            results.append(task.wait(timeout=timeout, die=die).result)
        except TimeoutError:
            continue
    return results
