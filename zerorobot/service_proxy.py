"""
This module implement the ServiceProxy class.

This class is used to provide a local proxy to a remote service for a ZeroRobot.
When a service or robot ask the creation of a service to another robot, a proxy class is created locally
so the robot see the service as if it as local to him while in reality the service is managed by another robot.
"""
import time

import gevent
from requests.exceptions import HTTPError

from js9 import j
from zerorobot.task import (Task, TASK_STATE_ERROR, TASK_STATE_NEW, TASK_STATE_OK,
                            TASK_STATE_RUNNING)
from zerorobot.template.state import ServiceState


class ServiceProxy():
    """
    This class is used to provide a local proxy to a remote service for a ZeroRobot.
    When a service or robot ask the creation of a service to another robot, a proxy class is created locally
    so the robot see the service as if it as local to him while in reality the service is managed by another robot.
    """

    def __init__(self, name, guid, zrobot_client):
        """
        @param name: name of the service
        @param guid: guid of the service
        @param zrobot_client: Instance of ZeroRobotClient that talks to the robot on which the
                              service is actually running
        """
        self._zrobot_client = zrobot_client
        self.name = name
        self.guid = guid
        self.template_uid = None
        self.parent = None
        # a proxy service doesn't have direct access to the data of it's remote homologue
        # cause data are always only accessible  by the service itself and locally
        self.data = None

    @property
    def state(self):
        # TODO: handle exceptions
        resp = self._zrobot_client.api.services.GetService(self.guid)
        s = ServiceState()
        for state in resp.data.state:
            s.set(state.category, state.tag, state.state.value)
        return s

    @property
    def task_list(self):
        resp = self._zrobot_client.api.services.getTaskList(service_guid=self.guid, query_params={'all': True})
        return _task_list_proxy_from_api(resp.data, self)

    def schedule_action(self, action, args=None, resp_q=None):
        """
        Do a call on a remote ZeroRobot to add an action to the task list of
        the corresponding service

        @param action: action is the name of the action to add to the task list
        @param args: dictionnary of the argument to pass to the action
        @param resp_q: is the response queue on which the result of the action need to be put
        """
        req = {
            "action_name": action,
        }
        if args:
            req["args"] = args
        try:
            resp = self._zrobot_client.api.services.AddTaskToList(req, service_guid=self.guid)
        except HTTPError as err:
            print(str(err.response.json()))
            raise err

        return _task_proxy_from_api(resp.data, self)

    def delete(self):
        self._zrobot_client.api.services.DeleteService(self.guid)


class TaskListProxy:

    def __init__(self):
        self._tasks = []
        self._done = []

    def empty(self):
        return len(self._tasks) == 0

    def list_tasks(self, all=False):
        tasks = list(self._tasks)
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

        task = find_task(guid, self._done)
        if task:
            return task
        task = find_task(guid, self._done)
        if task:
            return task
        raise KeyError("no task with guid %s found" % guid)


class TaskProxy(Task):
    """
    class that represent a task on a remote service

    the state attribute is an property that do an API call to get the
    actual state of the task on the remote ZeroRobot
    """

    def __init__(self, guid, service, action_name, args, created):
        super().__init__(service=service, action_name=action_name, args=args)
        self.guid = guid
        self._created = created

    def execute(self):
        raise RuntimeError("a TaskProxy should never be executed")

    @property
    def state(self):
        resp = self.service._zrobot_client.api.services.GetTask(
            task_guid=self.guid,
            service_guid=self.service.guid)
        return resp.data.state.value

    @state.setter
    def state(self, value):
        raise RuntimeError("you can't change the statet of a TaskProxy")


def _task_list_proxy_from_api(tasks, service):
    """
    instantiate an TaskListProxy from API response of
    GetTaskList call
    """
    task_list = TaskListProxy()
    for task in tasks:
        t = _task_proxy_from_api(task, service)

        if task.state.value in (TASK_STATE_ERROR, TASK_STATE_OK):
            task_list._done.append(t)
        elif task.state.value in (TASK_STATE_NEW, TASK_STATE_RUNNING):
            task_list._tasks.append(t)
    return task_list


def _task_proxy_from_api(task, service):
    t = TaskProxy(task.guid, service, task.action_name, task.args, task.created)
    if task.eco:
        d_eco = task.eco.as_dict()
        d_eco['_traceback'] = task.eco._traceback
        t.eco = j.core.errorhandler.getErrorConditionObject(ddict=d_eco)
    return t
