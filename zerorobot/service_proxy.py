"""
This module implement the ServiceProxy class.

This class is used to provide a local proxy to a remote service for a ZeroRobot.
When a service or robot ask the creation of a service to another robot, a proxy class is created locally
so the robot see the service as if it as local to him while in reality the service is managed by another robot.
"""

import urllib

from requests.exceptions import HTTPError

from jose import jwt
from js9 import j
from zerorobot.task import (TASK_STATE_ERROR, TASK_STATE_NEW, TASK_STATE_OK,
                            TASK_STATE_RUNNING, Task, TaskNotFoundError)
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
        # a proxy service doesn't have direct access to the data of it's remote homologue
        # cause data are always only accessible  by the service itself and locally
        self._data = None
        self.task_list = TaskListProxy(self)

    def __repr__(self):
        # Provide a nice representation in tools like IPython / js9
        return "robot://%s/%s?%s" % (self._zrobot_client.instance, self.template_uid, urllib.parse.urlencode(dict(name=self.name, guid=self.guid)))

    @property
    def data(self):
        return self._data

    @property
    def state(self):
        # TODO: handle exceptions
        service, _ = self._zrobot_client.api.services.GetService(self.guid)
        s = ServiceState()
        for state in service.state:
            s.set(state.category, state.tag, state.state.value)
        return s

    @property
    def actions(self):
        """
        list available actions of the services
        """
        actions, _ = self._zrobot_client.api.services.ListActions(self.guid)
        return sorted([a.name for a in actions])

    @property
    def logs(self):
        try:
            logs, resp = self._zrobot_client.api.services.GetLogs(self.guid)
        except HTTPError as err:
            if err.response.status_code == 400:
                raise RuntimeError(err.response.json()['message'])
            raise err

        return logs.logs

    def schedule_action(self, action, args=None):
        """
        Do a call on a remote ZeroRobot to add an action to the task list of
        the corresponding service

        @param action: action is the name of the action to add to the task list
        @param args: dictionnary of the argument to pass to the action
        """
        req = {
            "action_name": action,
        }
        if args:
            req["args"] = args
        task, _ = self._zrobot_client.api.services.AddTaskToList(req, service_guid=self.guid)

        return _task_proxy_from_api(task, self)

    def delete(self):
        self._zrobot_client.api.services.DeleteService(self.guid)
        # clean up secret from zrobot client
        for secret in list(self._zrobot_client.config.data['secrets_']):
            try:
                claims = jwt.get_unverified_claims(secret)
            except:
                continue
            else:
                if claims.get('service_guid') == self.guid:
                    self._zrobot_client.config.data['secrets_'].remove(secret)
                    self._zrobot_client.config.save()
                    return


class TaskListProxy:

    def __init__(self, service_proxy):
        self._service = service_proxy

    def empty(self):
        tasks, _ = self._service._zrobot_client.api.services.getTaskList(service_guid=self._service.guid, query_params={'all': False})
        return len(tasks) <= 0

    def list_tasks(self, all=False):
        tasks, _ = self._service._zrobot_client.api.services.getTaskList(service_guid=self._service.guid, query_params={'all': all})
        return [_task_proxy_from_api(t, self._service) for t in tasks]

    def get_task_by_guid(self, guid):
        """
        return a task from the list by it's guid
        """
        try:
            task, _ = self._service._zrobot_client.api.services.GetTask(service_guid=self._service.guid, task_guid=guid)
            return _task_proxy_from_api(task, self._service)
        except HTTPError as err:
            if err.response.status_code == 404:
                raise TaskNotFoundError("no task with guid %s found" % guid)
            raise err


class TaskProxy(Task):
    """
    class that represent a task on a remote service

    the state attribute is an property that do an API call to get the
    actual state of the task on the remote ZeroRobot
    """

    def __init__(self, guid, service, action_name, args, created):
        super().__init__(func=None, args=args)
        self.action_name = action_name
        self.service = service
        self.guid = guid
        self._created = created

    def execute(self):
        raise RuntimeError("a TaskProxy should never be executed")

    @property
    def result(self):
        if self._result is None:
            task, _ = self.service._zrobot_client.api.services.GetTask(task_guid=self.guid, service_guid=self.service.guid)
            if task.result:
                self._result = j.data.serializer.json.loads(task.result)
        return self._result

    @property
    def duration(self):
        if self._duration is None:
            task, _ = self.service._zrobot_client.api.services.GetTask(task_guid=self.guid, service_guid=self.service.guid)
            self._duration = task.duration
        return self._duration

    @property
    def state(self):
        task, _ = self.service._zrobot_client.api.services.GetTask(task_guid=self.guid, service_guid=self.service.guid)
        return task.state.value

    @state.setter
    def state(self, value):
        raise RuntimeError("you can't change the statet of a TaskProxy")

    @property
    def eco(self):
        if self._eco is None:
            task, _ = self.service._zrobot_client.api.services.GetTask(task_guid=self.guid, service_guid=self.service.guid)
            if task.eco:
                d_eco = task.eco.as_dict()
                d_eco['_traceback'] = task.eco._traceback
                self._eco = j.core.errorhandler.getErrorConditionObject(ddict=d_eco)
        return self._eco


def _task_proxy_from_api(task, service):
    t = TaskProxy(task.guid, service, task.action_name, task.args, task.created)
    if task.duration:
        t._duration = task.duration
    if task.eco:
        d_eco = task.eco.as_dict()
        d_eco['_traceback'] = task.eco._traceback
        t._eco = j.core.errorhandler.getErrorConditionObject(ddict=d_eco)
    return t
