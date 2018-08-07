import time
import unittest

from Jumpscale.errorhandling.ErrorConditionObject import ErrorConditionObject
from zerorobot.task.task import (TASK_STATE_ERROR, TASK_STATE_NEW,
                                 TASK_STATE_OK, TASK_STATE_RUNNING, Task)
from zerorobot.template.decorator import timeout


def noop():
    return "foo"


@timeout(10)
def with_decorator():
    return "foo"


@timeout(10)
def with_decorator_error():
    raise RuntimeError('oopsy daisy')


class TestTask(unittest.TestCase):

    def test_create_task(self):
        t = Task(noop, {})
        assert t.guid is not None
        assert t.state == TASK_STATE_NEW
        assert t._func == noop
        assert t.action_name == 'noop'
        assert t.created is not None and t.created < time.time()

    def test_execute_task(self):
        for func in [noop, with_decorator]:
            t = Task(noop, {})
            t.execute()
            assert t.duration > 0
            assert t.eco is None
            assert t.result == 'foo'
            assert t.state == TASK_STATE_OK

    def test_execute_error(self):
        t = Task(with_decorator_error, {})
        t.execute()
        assert t.state == TASK_STATE_ERROR
        assert t.eco is not None

        # task.wait should not raise is state is error but die is False
        t.wait(die=False)

        with self.assertRaises(ErrorConditionObject, message='task.wait should raise if state is error and die is True'):
            t.wait(die=True)
