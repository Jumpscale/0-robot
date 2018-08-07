# need to patch sockets to make requests async
from gevent import monkey
monkey.patch_all(subprocess=False)

import os
import shutil
import unittest
import uuid


from jumpscale import j
from Jumpscale.errorhandling.ErrorConditionObject import ErrorConditionObject
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot import config
from zerorobot.dsl.ZeroRobotManager import ZeroRobotManager
from zerorobot.robot import Robot
from zerorobot.service_proxy import ServiceProxy
from zerorobot.task.task import TASK_STATE_ERROR, TASK_STATE_OK


class TestServiceProxy(unittest.TestCase):

    def setUp(self):
        # make sure this test instance client exists
        j.clients.zrobot.get('test', {'url': 'http://localhost:6600'})
        self.cl = ZeroRobotManager('test')
        self.robot = Robot()
        self.robot.set_data_repo(j.sal.fs.getTmpDirPath())
        self.robot.add_template_repo('http://github.com/threefoldtech/0-robot', directory='tests/fixtures/templates')
        if os.path.exists(config.data_repo.path):
            shutil.rmtree(config.data_repo.path)
        # make sure we don't have any service loaded
        scol.drop_all()
        self.robot.start(listen='127.0.0.1:6600', block=False, testing=True)

    def tearDown(self):
        self.robot.stop(timeout=1)
        if os.path.exists(config.data_repo.path):
            shutil.rmtree(config.data_repo.path)
        j.clients.zrobot.delete('test')

    def _create_proxy(self, public=False):
        template = 'github.com/threefoldtech/0-robot/node/0.0.1'
        name = 'node1'
        proxy = self.cl.services.create(template, name, public=public)
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

        all_tasks_guid = [t.guid for t in proxy.task_list.list_tasks(True)]
        self.assertIn(task.guid, all_tasks_guid, "task create on service should be visible from the proxy")

        proxy_task = proxy.task_list.get_task_by_guid(task.guid)
        self.assertEqual(proxy_task.state, task.state, "state of a task should be reflect on the proxy task")

        self.assertEqual(proxy_task.result, task.result, "result on the proxy task should be the same as on the real task")
        self.assertEqual(proxy_task.created, task.created, "created time on the proxy task should be the same as on the real task")
        self.assertEqual(proxy_task.duration, task.duration, "duration on the proxy task should be the same as on the real task")

        proxy.schedule_action('stop')
        self.assertEqual(len(service.task_list.list_tasks(all=True)), 2, "task create on proxy should be visible on real service")

        # test task result for None result
        task = service.schedule_action('stop')
        task.wait()
        self.assertEqual(task.state, TASK_STATE_OK)
        proxy_task = proxy.task_list.get_task_by_guid(task.guid)
        self.assertEqual(proxy_task.result, task.result, "result on the proxy task should be the same as on the real task")

        # test eco attribute on proxy tasks
        task = service.schedule_action('error')
        task.wait()

        proxy_task = proxy.task_list.get_task_by_guid(task.guid)
        self.assertIsNotNone(proxy_task.eco)
        self.assertEqual(proxy_task.state, TASK_STATE_ERROR)

        # task.wait should not raise is state is error but die is False
        proxy_task.wait(die=False)

        with self.assertRaises(ErrorConditionObject, message='task.wait should raise if state is error and die is True'):
            proxy_task.wait(die=True)

    def test_delete(self):
        proxy, service = self._create_proxy()
        proxy.delete()
        with self.assertRaises(KeyError, msg='deleting a proxy, should delete the real service'):
            scol.get_by_guid(proxy.guid)

    def test_task_result(self):
        proxy, service = self._create_proxy()

        for ret_val in [False, '', None]:
            task = proxy.schedule_action('test_return', args={'return_val': ret_val})
            task.wait()
            assert task.result == ret_val

    def test_service_public(self):
        proxy, service = self._create_proxy(public=True)
        guids = list(self.cl.services.guids.keys())
        assert service.guid in guids

        self.cl._client.config.data_set('secrets_', [])
        self.cl._client._api = None  # force reload after we remove the secrets

        guids = list(self.cl.services.guids.keys())
        assert service.guid in guids, "service should still be visible for client that doe not have the secret of the service"
        assert proxy.actions != []
