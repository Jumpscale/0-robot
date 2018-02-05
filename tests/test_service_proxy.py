import os
import shutil
import unittest
import uuid

from gevent import monkey
from js9 import j
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot.dsl.ZeroRobotManager import ZeroRobotManager
from zerorobot.robot import Robot
from zerorobot.service_proxy import ServiceProxy

# need to patch sockets to make requests async
monkey.patch_all(subprocess=False)


class TestServiceProxy(unittest.TestCase):

    def setUp(self):
        # make sure this test instance client exists
        j.clients.zrobot.get('test', {'url': 'http://localhost:6600'})
        self.cl = ZeroRobotManager('test')
        self.robot = Robot()
        self.robot.set_data_repo('http://github.com/jumpscale/0-robot')
        self.robot.add_template_repo('http://github.com/jumpscale/0-robot', directory='tests/fixtures/templates')
        if os.path.exists(self.robot._data_dir):
            shutil.rmtree(self.robot._data_dir)
        # make sure we don't have any service loaded
        scol.drop_all()
        self.robot.start(listen='127.0.0.1:6600', block=False)

    def tearDown(self):
        self.robot.stop()
        shutil.rmtree(self.robot._data_dir)
        j.clients.zrobot.delete('test')

    def _create_proxy(self):
        template = 'github.com/jumpscale/0-robot/node/0.0.1'
        name = 'node1'
        proxy = self.cl.services.create(template, name)
        service = scol.get_by_guid(proxy.guid)
        return (proxy, service)

    def test_create_proxy(self):
        proxy, service = self._create_proxy()

        self.assertEqual(proxy.guid, service.guid, "proxy should have same guid as real service")
        self.assertEqual(proxy.name, service.name, "proxy should have same name as real service")
        self.assertIsNone(proxy.data, "proxy should not have access to the data of the services")

    def test_state(self):
        proxy, service = self._create_proxy()

        service.state.set('foo', 'bar', 'ok')
        self.assertDictEqual(service.state.categories, proxy.state.categories, "proxy state should reflect service state")

        service.state.set('foo', 'bar', 'error')
        self.assertEqual(proxy.state.get('foo', 'bar'), {'bar': 'error'}, 'update of service state, should be reflect in proxy')

        proxy.state.set('foo', 'bar', 'ok')
        self.assertNotEqual(service.state.get('foo', 'bar'), {'bar': 'ok'}, 'update of proxy state, should not be reflect in service')

    def test_task_list(self):
        proxy, service = self._create_proxy()

        task = service.schedule_action('start')
        task.wait()

        self.assertEqual(len(proxy.task_list.list_tasks(all=True)), 1, "task create on service should be visible from the proxy")
        proxy_task = proxy.task_list.get_task_by_guid(task.guid)
        self.assertEqual(proxy_task.state, task.state, "state of a task should be reflect on the proxy task")
        task.state = 'error'
        self.assertEqual(proxy_task.state, task.state, "state of a task should be reflect on the proxy task")

        self.assertEqual(proxy_task.result, task.result, "result on the proxy task should be the same as on the real task")

        proxy.schedule_action('stop')
        self.assertEqual(len(service.task_list.list_tasks(all=True)), 2, "task create on proxy should be visible on real service")

        # test task result for None result
        task = service.schedule_action('stop')
        task.wait()
        proxy_task = proxy.task_list.get_task_by_guid(task.guid)
        self.assertEqual(proxy_task.result, task.result, "result on the proxy task should be the same as on the real task")

    def test_delete(self):
        proxy, service = self._create_proxy()

        proxy.delete()
        with self.assertRaises(KeyError, msg='deleting a proxy, should delete the real service'):
            scol.get_by_guid(proxy.guid)
