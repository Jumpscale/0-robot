
import json
import os

import gevent
from gevent.queue import PriorityQueue

from js9 import j

from . import (PRIORITY_NORMAL, PRIORITY_SYSTEM, TASK_STATE_ERROR,
               TASK_STATE_NEW, TASK_STATE_OK, TASK_STATE_RUNNING)
from .storage.base import TaskNotFoundError
from .storage.sqlite import TaskStorageSqlite
# from .storage.file import TaskStorageFile
# from .storage.redis import TaskStorageRedis
from .task import Task
from .utils import _instantiate_task
from zerorobot.prometheus.robot import nr_task_waiting


class TaskList:
    """
    Task list if a FIFO queue of tasks
    """

    def __init__(self, service):
        self.service = service
        self._queue = PriorityQueue()
        # done keeps the tasks that have been extracted from the queue
        # so we can inspect them later

        # keep the done task on disk, not in memory.
        # now we use the filesystem, but we could plug any key-value stor or database behind
        # check TaskStorageBase to see the interface your storage needs to have
        # to be used to store tasks
        # self._done = TaskStorageFile(self)
        self._done = TaskStorageSqlite(self)
        # pointer to current task
        self.current = None

    def __del__(self):
        if self._done:
            self._done.close()

    def get(self):
        """
        pop out a task from the task list
        this call is blocking when the task list is empty
        """
        _, task = self._queue.get()
        self.current = task
        nr_task_waiting.labels(service_guid=self.service.guid).dec()
        return task

    def put(self, task, priority=PRIORITY_NORMAL):
        """
        append task to the task list
        """
        if not isinstance(task, Task):
            raise ValueError("task should be an instance of the Task class not %s" % type(task))
        task._priority = priority
        nr_task_waiting.labels(service_guid=self.service.guid).inc()
        self._queue.put((priority, task))

    def done(self, task):
        """
        notify that a task is done
        """
        if task._priority != PRIORITY_SYSTEM:
            self.current = None
            self._done.add(task)

    def empty(self):
        """
        return True if the task list is empty, False otherwise
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
            tasks.extend(self._done.list())

        if self.current and self.current.state == TASK_STATE_RUNNING:
            # also return the current running
            # task as part of the task list
            tasks.insert(0, self.current)

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
            raise TaskNotFoundError()

        # check if it's not the current running task
        if self.current and self.current.guid == guid:
            return self.current

        # search in waiting tasks
        try:
            task = find_task(guid, [x[1] for x in self._queue.queue])
            return task
        except TaskNotFoundError:
            pass

        # search in done task
        # this will raise TaskNotFoundError if can't find the task
        return self._done.get(guid)

    def save(self, path):
        """
        serialize the task list to disk
        @param path: file path where to serialize the task list
        """
        def serialize_task(task):
            return {
                "guid": task.guid,
                "action_name": task.action_name,
                "args": task._args,
                "state": task.state,
                "eco": json.loads(task.eco.json) if task.eco else None,
                "created": task.created,
            }
        output = []
        for task in self.list_tasks(all=False):
            output.append(serialize_task(task))
        j.data.serializer.yaml.dump(path, output)

    def load(self, path):
        """
        load a task list that have been serialized with save method
        @param path: file path where the task list is serialized
        @param service: the service object to which this task list belongs
        """
        if not os.path.exists(path):
            return

        data = j.data.serializer.yaml.load(path)
        for task in data:
            if task['state'] in [TASK_STATE_NEW, TASK_STATE_RUNNING]:
                self.put(_instantiate_task(task, self.service))
            else:
                # None supported state, just skip it
                continue
