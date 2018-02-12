"""
task module holds the logic regarding TaskList and Task classes.

These two classes are used by the services to managed the requested actions
"""

import json
import os
import sys
import time

import gevent
from gevent.lock import Semaphore
from gevent.queue import PriorityQueue
from js9 import j

from zerorobot.prometheus.robot import nr_task_waiting


# Task state constant
TASK_STATE_NEW = "new"
TASK_STATE_RUNNING = "running"
TASK_STATE_OK = "ok"
TASK_STATE_ERROR = "error"


logger = j.logger.get('zerorobot')


class Task:

    def __init__(self, func, args):
        """
        @param service: is the service object that own the action to be executed
        @param action_name: is the method name of the action that this task need to execute
        @param args: argument to pass to the action when executing
        """
        self.guid = j.data.idgenerator.generateGUID()
        self.func = func
        self.action_name = func.__name__ if func else None
        self._args = args
        self._created = time.time()
        self._result = None

        # used when action raises an exception
        self.eco = None

        self._state = TASK_STATE_NEW
        self._state_lock = Semaphore()

    @property
    def created(self):
        return int(self._created)

    @property
    def result(self):
        return self._result

    def execute(self):

        self.state = TASK_STATE_RUNNING
        # TODO: handle logging,...
        result = None

        try:
            if self._args is not None:
                self._result = self.func(**self._args)
            else:
                self._result = self.func()
            self.state = TASK_STATE_OK
        except Exception as err:
            self.state = TASK_STATE_ERROR
            # capture stacktrace and exception
            _, _, exc_traceback = sys.exc_info()
            self.eco = j.core.errorhandler.parsePythonExceptionObject(err, tb=exc_traceback)
            self.eco.printTraceback()
        return result

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        try:
            self._state_lock.acquire()
            self._state = value
        finally:
            self._state_lock.release()

    def wait(self, timeout=None):
        """
        wait blocks until the task has been executed
        if timeout is specified and the task didn't finished within timeout seconds,
        raises TimeoutError
        """
        def wait():
            while self.state in ('new', 'running'):
                gevent.sleep(0.5)

        if timeout:
            # ensure the type is correct
            timeout = float(timeout)
            try:
                gevent.with_timeout(timeout, wait)
            except gevent.Timeout:
                raise TimeoutError()
        else:
            wait()

    def __lt__(self, other):
        return self._created < other._created

    def __repr__(self):
        return self.action_name

    def __str__(self):
        return repr(self)


# has the highest priority, usually used by the robot when it needs a service to execute something
PRIORITY_SYSTEM = 0
# priority used for recurring action, need to be higher then normal actions
PRIORITY_RECURRING = 5
# default value used when an action is schedule from normal user API
PRIORITY_NORMAL = 10


class TaskList:
    """
    Task list if a FIFO queue of tasks
    """

    def __init__(self, service):
        self._queue = PriorityQueue()
        self._service = service
        # done keeps the tasks that have been extracted from the queue
        # so we can inspect them later
        # TODO: done tasks should be kept on disk, not in memory
        self._done = []

    def get(self):
        """
        pop out a task from the task list
        this call is blocking when the task list is empty
        """
        priority, task = self._queue.get()
        # only keep non system task into the done task list
        if priority != PRIORITY_SYSTEM:
            self._done.append(task)

        nr_task_waiting.labels(service_guid=self._service.guid).dec()
        return task

    def put(self, task, priority=PRIORITY_NORMAL):
        """
        append task to the task list
        """
        if not isinstance(task, Task):
            raise ValueError("task should be an instance of the Task class not %s" % type(task))
        nr_task_waiting.labels(service_guid=self._service.guid).inc()
        self._queue.put((priority, task))

    def empty(self):
        """
        return True is the task list is empty, False otherwise
        """
        return self._queue.empty()

    def list_tasks(self, all=False):
        """
        @param all: if True, also return the task that have been executed
                    if False only return the task waiting in the task list
        returns all the task that are currently in the task list
        """
        tasks = [x[1] for x in self._queue.queue]
        if all:
            tasks.extend(self._done)
        elif len(self._done) > 1 and self._done[-1].state == TASK_STATE_RUNNING:
            # also return the current running
            # task as part of the task list
            tasks.insert(0, self._done[-1])
        return tasks

    def get_task_by_guid(self, guid):
        """
        return a task from the list by it's guid
        """
        # FIXME: this is really inefficient
        def find_task(guid, l):
            for task in l:
                if task.guid == guid:
                    return task

        task = find_task(guid, [x[1] for x in self._queue.queue])
        if task:
            return task
        task = find_task(guid, self._done)
        if task:
            return task
        raise KeyError("no task with guid %s found" % guid)

    def save(self, path):
        """
        serialize the task list to disk
        @param path: file path where to serialize the task list
        """
        def serialize_task(task):
            return {
                "guid": task.guid,
                # "service": = task.service.name,
                "action_name": task.action_name,
                "result": task._result,
                "args": task._args,
                "state": task.state,
                "eco": json.loads(task.eco.toJson()) if task.eco else None,
            }
        # FIXME: stream into file instead, this can consume a lot
        # of memory in case lots of tasks
        output = []
        for task in self.list_tasks(all=True):
            output.append(serialize_task(task))
        j.data.serializer.yaml.dump(path, output)

    def load(self, path, service):
        """
        load a task list that have been serialized with save method
        @param path: file path where the task list is serialized
        @param service: the service object to which this task list belongs
        """
        def instantiate_task(task):
            func = getattr(service, task['action_name'])
            t = Task(func, task['args'])
            if task['state'] in [TASK_STATE_RUNNING, TASK_STATE_NEW]:
                t.state = TASK_STATE_NEW
            else:
                t.state = task['state']
            t.guid = task['guid']
            t._result = task['result']
            if task['eco']:
                t.eco = j.core.errorhandler.getErrorConditionObject(ddict=task['eco'])
            return t

        if not os.path.exists(path):
            return

        data = j.data.serializer.yaml.load(path)
        for task in data:
            if task['state'] in [TASK_STATE_NEW, TASK_STATE_RUNNING]:
                self.put(instantiate_task(task))
            elif task['state'] in [TASK_STATE_OK, TASK_STATE_ERROR]:
                self._done.append(instantiate_task(task))
            else:
                # None supported state, just skip it
                continue
