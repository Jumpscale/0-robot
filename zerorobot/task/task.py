"""
task module holds the logic regarding TaskList and Task classes.

These two classes are used by the services to managed the requested actions
"""

import hashlib
import logging
import os
import pprint
import sys
import time
import traceback

import gevent
import requests
from gevent.lock import Semaphore

from js9 import j
from zerorobot import config
from zerorobot.errors import ExpectedError

from . import (TASK_STATE_ERROR, TASK_STATE_NEW, TASK_STATE_OK,
               TASK_STATE_RUNNING)

logger = j.logger.get('zerorobot')
telegram_logger = logging.getLogger('telegram_logger')

stacks = list()


class Task:

    def __init__(self, func, args):
        """
        @param func: action that needs to be called
        @param action_name: arguments for the action
        @param args: argument to pass to the action when executing
        """
        self.guid = j.data.idgenerator.generateGUID()
        self.service = None
        self._func = func
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
        started = time.time()
        try:
            if self._args is not None:
                self._result = self._func(**self._args)
            else:
                self._result = self._func()
            self.state = TASK_STATE_OK
        except:
            self.state = TASK_STATE_ERROR
            # capture stacktrace and exception
            exc_type, exc, exc_traceback = sys.exc_info()
            self._eco = j.core.errorhandler.parsePythonExceptionObject(exc, tb=exc_traceback)
            if not isinstance(exc, ExpectedError):
                gevent.spawn(self._report_telegram, exc_type, exc, exc_traceback)
                gevent.spawn(_send_eco_webhooks, self.service, self)
        finally:
            self._duration = time.time() - started
        return self._result

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

    def wait(self, timeout=None, die=False):
        """
        wait blocks until the task has been executed
        if timeout is specified and the task didn't finished within timeout seconds,
        raises TimeoutError

        if die is True and the state is TASK_STATE_ERROR after the wait, the eco of the exception will be raised
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

        if die is True and self.state == TASK_STATE_ERROR:
            if not self.eco:
                logger.critical('task is in error state, but no eco')
            else:
                raise self.eco

        return self

    def __lt__(self, other):
        return self._created < other._created

    def __repr__(self):
        return self.action_name

    def __str__(self):
        return repr(self)

    def _report_telegram(self, exc_type, exc, tb):
        # if enabled, unexpected errors would be logged on the telegram chat
        # go to last traceback
        last_traceback = tb
        while last_traceback.tb_next:
            last_traceback = last_traceback.tb_next

        # get locals
        locals_ = last_traceback.tb_frame.f_locals

        stacktrace = ''.join(traceback.format_tb(tb))
        stacktrace_hash = hashlib.md5(stacktrace.encode('utf8')).digest()
        if not stacktrace_hash in stacks:
            try:
                telegram_logger.error(
                    "Error type: %s\nError message:\n\t%s\nStacktrace:\n%s\n\nTask arguments:\n%s\n\nLocal values:\n%s" % (
                        exc_type.__name__,
                        exc,
                        stacktrace,
                        pprint.pformat(self._args, width=50),
                        pprint.pformat(locals_, width=50)
                    ))
                stacks.append(stacktrace_hash)
                while len(stacks) > 1000:
                    stacks.pop(0)
            except:
                logger.exception("Failed to log error to telegram handler")


def _send_eco_webhooks(service, task):
    if task.eco is None:
        return

    webhooks = config.webhooks

    # TODO: send concurrently from a pool of greenlet
    task.eco.key  # make sure uniquekey is filled
    eco_data = task.eco.__dict__.copy()
    eco_data.pop('tb', None)

    data = {
        'service': service.guid,
        'action_name': task.action_name,
        'args': task._args,
        'eco': eco_data
    }

    for wh in webhooks.list(kind='eco'):
        try:
            requests.post(wh.url, json=data)
            logger.debug("eco web hook sent to %s" % wh.url)
        except Exception as err:
            logger.warning('fail to send web hook to %s' % wh.url)
