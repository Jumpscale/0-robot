import os
import shutil
import tempfile
import unittest

from zerorobot import service_collection as scol
from zerorobot import config
from zerorobot.task import (PRIORITY_NORMAL, PRIORITY_SYSTEM, Task, TaskList,
                            TaskNotFoundError)
from zerorobot.template_collection import _load_template


class FakeService:

    def __init__(self, guid):
        self.guid = guid
        self.name = guid

    def foo(self):
        pass

    def bar(self):
        pass


class TestTaskList(unittest.TestCase):

    def setUp(self):
        config.DATA_DIR = tempfile.mkdtemp(prefix='0robottest')
        scol.drop_all()
        tmpl = self._load_template('node')
        s = tmpl(name='test')
        self.tl = TaskList(s)
        # ensure we have a clean start
        self.tl._done.drop()

    def tearDown(self):
        try:
            self.tl._done.close()
        finally:
            if os.path.exists(config.DATA_DIR):
                shutil.rmtree(config.DATA_DIR)

    def _load_template(self, name):
        """
        name of the template to load from the
        fixtures/templates folder
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        tmpl = _load_template("https://github.com/jumpscale/0-robot",
                              os.path.join(dir_path, 'fixtures', 'templates', name))
        return tmpl

    def _get_tasks(self, nr):
        tasks = []
        for i in range(nr):
            s = FakeService("s%d" % i)
            t = Task(s.foo, {})
            tasks.append(t)
        return tasks

    def test_create_list(self):
        self.assertIsNotNone(self.tl._queue)
        self.assertIsNotNone(self.tl._done)
        self.assertTrue(self.tl.empty())

    def test_put(self):
        with self.assertRaises(ValueError, msg="should raise when trying to put an object that is not a Task"):
            self.tl.put('string')

        self.assertTrue(self.tl.empty())
        srv = FakeService('s1')
        t = Task(srv.foo, {})
        self.tl.put(t)
        self.assertFalse(self.tl.empty())
        t2 = self.tl.get()
        self.tl.done(t2)
        self.assertEqual(t, t2, "task extracted from the list should be the same as the task added")
        self.assertEqual(self.tl._done.list()[0].guid, t.guid, "task extracted from the list should be kept in the _done list")

    def test_get(self):
        tasks = self._get_tasks(3)
        for t in tasks:
            self.tl.put(t)

        returned_tasks = []
        while not self.tl.empty():
            returned_tasks.append(self.tl.get())
        self.assertEqual(returned_tasks, tasks)

    def test_get_by_guid(self):
        tasks = self._get_tasks(3)
        for t in tasks:
            self.tl.put(t)

        t1 = tasks[0]

        task = self.tl.get_task_by_guid(t1.guid)
        self.assertEqual(task, t1)

        with self.assertRaises(TaskNotFoundError):
            self.tl.get_task_by_guid('1111')

    def test_list(self):
        tasks = self._get_tasks(2)
        for t in tasks:
            self.tl.put(t)

        returned_tasks = self.tl.list_tasks()
        self.assertEqual(returned_tasks, tasks, "listing of tasks should return all enqueued tasks")

        task = self.tl.get()
        self.tl.done(task)
        returned_tasks = self.tl.list_tasks()
        self.assertEqual(returned_tasks, tasks[1:], "listing of tasks should return all enqueued tasks")

        all_tasks = [t.guid for t in self.tl.list_tasks(all=True)]
        self.assertEqual(all_tasks, [t.guid for t in reversed(tasks)], "listing of all tasks should return all enqueued tasks and all done tasks")

    def test_priority(self):

        s1 = FakeService("s1")
        s2 = FakeService("s2")
        s3 = FakeService("s3")

        t1 = Task(s1.foo, {})
        t2 = Task(s1.foo, {})
        t3 = Task(s1.foo, {})

        self.tl.put(t1, priority=PRIORITY_NORMAL)
        self.tl.put(t2, priority=PRIORITY_NORMAL)
        self.tl.put(t3, priority=PRIORITY_SYSTEM)

        tasks = []
        while not self.tl.empty():
            tasks.append(self.tl.get())

        self.assertEqual(tasks, [t3, t1, t2], "task with higher priority should be extracted first")
