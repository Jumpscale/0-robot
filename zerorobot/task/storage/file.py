from .base import TaskStorageBase, TaskNotFoundError
from zerorobot.task.utils import _instantiate_task
import os

from js9 import j


class TaskStorageFile(TaskStorageBase):
    """
    This class implement the TaskStorage interface
    using simple file on the local filesystem
    """

    def __init__(self, task_list):
        self.service = task_list.service
        # self._root = j.sal.fs.getTmpDirPath()
        self._root = os.path.join(self.service._path, 'tasks')
        if not os.path.exists(self._root):
            os.makedirs(self._root)
        self._count = 0

    def add(self, task):
        """
        save a task to the storage
        """
        self._count += 1
        path = os.path.join(self._root, "%d_%s" % (self._count, task.guid))
        j.sal.fs.writeFile(path, self._serialize_task(task))

    def get(self, guid):
        """
        find a task by guid
        """
        results = j.sal.fs.find(self._root, '*_%s' % guid)
        if len(results) <= 0:
            raise TaskNotFoundError("task %s not found" % guid)
        if len(results) > 1:
            raise RuntimeError("found 2 tasks with same guid, this should not happen")
        return self._deserialize_task(j.sal.fs.readFile(results[0]))

    def list(self, from_timestap=None, to_timestap=None):
        """
        list all task. Optionally filter on time of creation
        from_timestamp: filter all task created before from_timetamp
        to_timestamp: filter all task created after to_timestamp
        """
        tasks = []
        for path in j.sal.fs.listFilesInDir(self._root):
            blob = j.sal.fs.readFile(path)
            task = self._deserialize_task(blob)
            if from_timestap and task.created < from_timestap:
                continue
            if to_timestap and task.created > to_timestap:
                continue
            tasks.append(task)
        return tasks

    def count(self):
        """
        return the number of task stored
        """
        return self._count

    def close(self):
        """
        gracefully close storage
        """
        pass

    def drop(self):
        """
        delete all the tasks
        """
        j.sal.fs.removeDirTree(self._root, True)
        j.sal.fs.createDir(self._root)

    def _serialize_task(self, task):
        return j.data.serializer.json.dumps({
            "guid": task.guid,
            "action_name": task.action_name,
            "args": task._args,
            "state": task.state,
            "eco": j.data.serializer.json.loads(task.eco.toJson()) if task.eco else None,
            "result": task.result,
        })

    def _deserialize_task(self, blob):
        task = j.data.serializer.json.loads(blob)
        return _instantiate_task(task, self.service)
