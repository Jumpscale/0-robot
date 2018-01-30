class TaskStorageBase:
    """
    This is the base class that need to be implemented
    in order to store task on different medium
    """

    def __init__(self, task_list):
        """
        create connection to the storage

        @param task_list: a pointer to the task_list that is using this storage
        """
        self.task_list = task_list

    def add(self, task):
        """
        save a task to the storage
        """
        raise NotImplementedError()

    def get(self, guid):
        """
        find a task by guid,
        if not found should raise TaskNotFoundError
        """
        raise NotImplementedError()

    def list(self, from_timestap=None, to_timestap=None):
        """
        list all task. Optionally filter on time of creation
        from_timestamp: filter all task created before from_timetamp
        to_timestamp: filter all task created after to_timestamp
        """
        raise NotImplementedError()

    def count(self):
        """
        return the number of task stored
        """
        raise NotImplementedError()

    def close(self):
        """
        gracefully close storage
        """
        raise NotImplementedError()


class TaskNotFoundError(Exception):
    pass
