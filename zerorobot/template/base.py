"""
The base module defines the TemplateBase class.
It is the class every template should inherits from.
"""

import glob
import inspect
import logging
import os
import pprint
import shutil
import time
from logging.handlers import RotatingFileHandler
from uuid import uuid4

import gevent

from js9 import j
from zerorobot import service_collection as scol
from zerorobot import config
from zerorobot.dsl.ZeroRobotAPI import ZeroRobotAPI
from zerorobot.prometheus.robot import task_latency
from zerorobot.task import (PRIORITY_NORMAL, PRIORITY_SYSTEM, TASK_STATE_ERROR,
                            Task, TaskList)
from zerorobot.template.data import ServiceData
from zerorobot.template.state import ServiceState

logger = j.logger.get('zerorobot')


class BadActionArgumentError(Exception):
    """
    Error return when the argument pass when trying to schedule an action
    doesn't match with the method signature
    """
    pass


class ActionNotFoundError(Exception):
    """
    Error raised when trying to schedule an action that doesn't exist
    """
    pass


class GreenletsMgr:
    """
    GreenletsMgr is a tools that lets you
    manage a group of greenlets

    it gives basic primitives to keep a reference of a greenlets and start/stop/get them
    """

    def __init__(self):
        self.gls = {}

    def add(self, key, func, *args, **kwargs):
        """
        keep reference of a new greenlet
        @param key: unique identifier of the greenlet, you need it to stop the greenlet
        @param func: a callable or a gevent.Greenlet
                    if a callable, create a greenlet with it
                    if a greenlet, just make sure that it's started
        """
        if isinstance(func, gevent.Greenlet):
            gl = func
        else:
            if not callable(func):
                raise TypeError("gl should be a callable or a gevent.Greenlet not %s" % type(func))
            gl = gevent.Greenlet(func, *args, **kwargs)

        if not gl.started:
            gl.start()

        self.gls[key] = gl

    def get(self, key):
        return self.gls[key]

    def stop(self, key):
        try:
            gl = self.get(key)
            gl.kill()
            del self.gls[key]
        except KeyError:
            pass

    def stop_all(self, wait=False):
        for gl in self.gls.values():
            gl.kill()
        if wait:
            gevent.wait(list(self.gls.values()))


class TemplateBase:
    """
    This is the base class any service should inherit from.

    The child class will implement actions on this class.
    """

    # The developer of the template need to set the version the template
    version = None
    # This is the unique identifier of the template. This is set during template loading
    template_uid = None
    # path of the template on disk. This is set during template loading
    template_dir = None

    def __init__(self, name=None, guid=None, data=None):
        self.template_dir = os.path.dirname(inspect.getsourcefile(self.__class__))
        self.guid = guid or str(uuid4())
        self.name = name or self.guid
        self.parent = None
        # location on the filesystem where to store the service
        self._path = os.path.join(
            config.DATA_DIR,
            self.template_uid.host,
            self.template_uid.account,
            self.template_uid.repo,
            self.template_uid.name,
            self.name,
            self.guid
        )

        self.api = ZeroRobotAPI()

        self.data = ServiceData(self)
        if data:
            self.data.update(data)
        self.state = ServiceState()
        self.task_list = TaskList(self)

        # start the greenlets of this service
        self.gl_mgr = GreenletsMgr()
        self.gl_mgr.add('executor', gevent.Greenlet(self._run))
        self.recurring_action('save', 10)

        self.logger = _configure_logger(self.guid)

    def validate(self):
        """
        This method is called on all services during robot statup
        after all the service have been loaded

        in here you can implement some logic to ensure that all the requirement
        of you service are still met after a restart of the 0-robot
        """
        pass

    def save(self):
        """
        serialize the service state and data to a file

        @param base_path: path of the directory where
                          to save the service state and data
        return the path where the service is saved
        """
        if self._path is None:
            raise RuntimeError("service._path is None, don't know where to save the service")

        # if base_path is not None and base_path != '':
        #     parent = self.parent
        #     path = base_path
        #     while parent is not None:
        #         path = os.path.join(path, parent.name)
        #         parent = parent.parent

        #     path = os.path.join(path, self.guid)
        #     self._path = path
        # else:
        #     path = self._path

        os.makedirs(self._path, exist_ok=True)

        j.data.serializer.yaml.dump(os.path.join(self._path, 'service.yaml'), {
            'template': str(self.template_uid),
            'version': self.version,
            'name': self.name,
            'guid': self.guid,
            'parent': self.parent.guid if self.parent else None,
        })
        self.state.save(os.path.join(self._path, 'state.yaml'))
        self.data.save(os.path.join(self._path, 'data.yaml'))
        self.task_list.save(os.path.join(self._path, 'tasks.yaml'))
        return self._path

    def _run(self):
        """
        _run is responsible to walk over the task list to execute actions
        and handle responses from other service
        """
        while True:
            task = None
            try:
                task = self.task_list.get()
                task.execute()
            except gevent.GreenletExit:
                # TODO: gracefull shutdown
                break
            finally:
                if task:
                    task_latency.labels(action_name=task.action_name, template_uid=str(self.template_uid)).observe(task.duration)
                    # notify the task list that this task is done
                    self.task_list.done(task)
                    if task.state == TASK_STATE_ERROR:
                        tb = task.eco.traceback

                        self.logger.error("error executing action %s:\n%s" % (task.action_name, task.eco.traceback))

                        # go to last traceback
                        while tb.tb_next:
                            tb = tb.tb_next

                        # get locals
                        locals = tb.tb_frame.f_locals

                        # if enable, this would be logged on the telegram chat
                        self.logger.critical(
                            "Error executing action %s:\n%s\n\nLocal values:\n%s" % (
                                task.action_name,
                                tb,
                                pprint.pformat(locals, width=50)
                            ))

    def schedule_action(self, action, args=None):
        """
        Add an action to the task list of this service.
        This method should never be called directly by the user.
        It will always be called by another service.
        Or from a local service or from a remote service trough RPC

        @param action: action is the name of the action to add to the task list
        @param args: dictionnary of the argument to pass to the action
        """
        return self._schedule_action(action, args)

    def _schedule_action(self, action, args=None, priority=PRIORITY_NORMAL):
        if not hasattr(self, action):
            raise ActionNotFoundError("service %s doesn't have action %s" % (self.name, action))

        method = getattr(self, action)
        if not callable(method):
            raise ActionNotFoundError("%s is not a function" % action)

        # make sure the argument we pass are correct
        kwargs_enable = False
        s = inspect.signature(method, follow_wrapped=True)
        for param in s.parameters.values():
            if param.kind == param.VAR_KEYWORD:
                kwargs_enable = True
            if args is None:
                args = {}
            if param.default == s.empty and param.name not in args and param.kind != param.VAR_KEYWORD:
                raise BadActionArgumentError("parameter %s is mandatory but not passed to in args" % param.name)

        if args is not None:
            signature_keys = set(s.parameters.keys())
            args_keys = set(args.keys())
            diff = args_keys.difference(signature_keys)
            if diff and not kwargs_enable:
                raise BadActionArgumentError('arguments "%s" are not present in the signature of the action' % ','.join(diff))

        task = Task(method, args)
        self.task_list.put(task, priority=priority)
        return task

    def recurring_action(self, action, period):
        """
        configure an action to be executed every period second

        It will ensure that the action from service is schedule at best every period second.

        Since we dont' have control over how long other task from the task list take.
        we can only ensure that the action is never going to be schedule faster then every period second

        That means that it can be a longer time then period second during which the action is not executed

        @param action: a method or string that match the name of the method we want to make recurring
        @param period: minimum number of seconds between 2 scheduling of the action
        """
        if inspect.ismethod(action) or inspect.isfunction(action):
            action = action.__name__

        gl = gevent.Greenlet(_recurring_action, self, action, period)
        self.gl_mgr.add("recurring_" + action, gl)

    def delete(self):
        """
        Delete the service.

        If you overwrite this method in your template,
        make sure to always call this method at the end of your method
        e.g: super().delete()
        """
        self.logger.info("deleting service %s (%s)", self.name, self.guid)
        # stop all recurring action
        self.gl_mgr.stop_all(wait=True)

        # close ressources of logging handlers
        for h in self.logger.handlers:
            if hasattr(h, 'close'):
                h.close()

        # remove data from disk
        if self._path and os.path.exists(self._path):
            shutil.rmtree(self._path)

        # remove logs from disk
        log_file = os.path.join(j.dirs.LOGDIR, 'zrobot', self.guid)
        for f in glob.glob(log_file+'*'):
            os.remove(f)

        # remove from memory
        scol.delete(self)

    def update_data(self, data):
        """
        This method needs to be implement by child class
        when you want to control the update of the schema data

        This method is called everytime the schema data is changed
        by a blueprint.

        @param data: is a dict with the new schema data
        """
        self.data.update(data)


def _recurring_action(service, action, period):
    """
    this function is intended to be run in a greenlet.
    It will ensure that the action from service is schedule at best every period second.

    Since we dont' have controle over how long other task from the task list take.
    we can only ensure that the action is never going to be schedule faster then every period second

    That means that it can be a longer time then period second during which the action is not executed
    """
    elapsed = -1
    while True:
        tasks_name = [t.action_name for t in service.task_list.list_tasks()]
        try:
            # schedule if period time has elasped and the same action is not already in the task list
            if elapsed == -1 or elapsed >= period and action not in tasks_name:
                task = service._schedule_action(action, priority=PRIORITY_SYSTEM)
                task.wait()
                last = time.time()
            else:
                gevent.sleep(0.5)

            elapsed = int(time.time()) - task.created
        except gevent.GreenletExit:
            break


_LOGGER_FORMAT = '%(asctime)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s'


def _configure_logger(guid):
    log_dir = os.path.join(j.dirs.LOGDIR, 'zrobot')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    l = logging.getLogger('service-%s' % guid)
    l.parent.handlers = []
    rfh = RotatingFileHandler(os.path.join(log_dir, guid),
                              mode='a',
                              maxBytes=512 * 1024,  # 512k
                              backupCount=1,  # 2 * 512k = 1Mib of logs max per service
                              encoding=None,
                              delay=True)
    rfh.setLevel(logging.DEBUG)
    rfh.setFormatter(logging.Formatter(_LOGGER_FORMAT))
    l.addHandler(rfh)
    for h in j.logger.handlers._all:
        l.addHandler(h)
    l.setLevel(logging.DEBUG)
    return l
