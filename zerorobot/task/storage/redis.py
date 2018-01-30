
from js9 import j

from .base import TaskNotFoundError
from zerorobot.task.utils import _instantiate_task


class TaskStorageRedis:
    """
    This class implement the TaskStorage interface
    using simple file on the local filesystem
    """

    def __init__(self, task_list):
        """
        create connection to the storage
        """
        super().__init__()
        self._service = task_list._service
        self._namespace = task_list._service.guid
        self._redis = j.clients.redis.get()

    def add(self, task):
        """
        save a task to the storage
        """
        self._redis.hset(self._namespace, task.guid, self._serialize_task(task))

    def get(self, guid):
        """
        find a task by guid
        """
        blob = self._redis.hget(self._namespace, guid)
        if blob:
            return self._deserialize_task(blob)
        raise TaskNotFoundError()

    def list(self, from_timestap=None, to_timestap=None):
        """
        list all task. Optionally filter on time of creation
        from_timestamp: filter all task created before from_timetamp
        to_timestamp: filter all task created after to_timestamp
        """
        tasks = []
        for blob in self._redis.hgetall(self._namespace).values():
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
        return self._redis.hlen(self._namespace)

    def close(self):
        """
        gracefully close storage
        """
        if self._redis:
            self._redis.delete(self._namespace)
            self._redis = None

    def _serialize_task(self, task):
        return j.data.serializer.json.dumps({
            "guid": task.guid,
            "action_name": task.action_name,
            "args": task._args,
            "state": task.state,
            "eco": j.data.serializer.json.loads(task.eco.toJson()) if task.eco else None,
        })

    def _deserialize_task(self, blob):
        task = j.data.serializer.json.loads(blob)
        return _instantiate_task(task, self._service)
