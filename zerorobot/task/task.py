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

from js9 import j

from . import (TASK_STATE_ERROR, TASK_STATE_NEW, TASK_STATE_OK,
               TASK_STATE_RUNNING)


class Task:

    def __init__(self, func, args, resp_q=None):
        """
        @param service: is the service object that own the action to be executed
        @param action_name: is the method name of the action that this task need to execute
        @param args: argument to pass to the action when executing
        @param resp_q: is the response queue on which the result of the action need to be put
        """
        self.guid = j.data.idgenerator.generateGUID()
        self.func = func
        self.action_name = func.__name__ if func else None
        self._args = args
        self._priority = None
        self._result = None
        self._created = time.time()
        self._duration = None

        # used when action raises an exception
        self._eco = None

        self._state = TASK_STATE_NEW
        self._state_lock = Semaphore()

    @property
    def created(self):
        return int(self._created)

    @property
    def duration(self):
        return self._duration

    @property
    def result(self):
        return self._result

    @property
    def eco(self):
        return self._eco

    def execute(self):

        self.state = TASK_STATE_RUNNING
        # TODO: handle logging,...
        result = None
        started = time.time()
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
            self._eco = j.core.errorhandler.parsePythonExceptionObject(err, tb=exc_traceback)
            self._eco.printTraceback()
        finally:
            self._duration = time.time() - started

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
