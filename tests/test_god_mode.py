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
from zerorobot.server.auth import god_jwt
from zerorobot.server import auth


class RobotContext:

    def __init__(self, god):
        self.god = god

    def __enter__(self):
        j.clients.zrobot.get('test', {'url': 'http://localhost:6600'})
        self.cl = ZeroRobotManager('test')
        self.robot = Robot()

        self.robot.set_data_repo(j.sal.fs.getTmpDirPath())
        self.robot.add_template_repo('http://github.com/threefoldtech/0-robot', directory='tests/fixtures/templates')
        if os.path.exists(config.data_repo.path):
            shutil.rmtree(config.data_repo.path)
        # make sure we don't have any service loaded
        scol.drop_all()
        self.robot.start(listen='127.0.0.1:6600', block=False, testing=True, god=self.god)
        return self.cl

    def __exit__(self, type, value, tb):
        self.robot.stop(timeout=1)
        if os.path.exists(config.data_repo.path):
            shutil.rmtree(config.data_repo.path)
        j.clients.zrobot.delete('test')


class TestGodMode(unittest.TestCase):

    def create_proxy(self, client, public=False):
        template = 'github.com/threefoldtech/0-robot/node/0.0.1'
        name = 'node1'
        proxy = client.services.create(template, name, public=public)
        service = scol.get_by_guid(proxy.guid)
        return (proxy, service)

    def test_read_data_god_enabled_token_valid(self):
        god_token = god_jwt.create()
        with RobotContext(god=True) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)

            assert proxy.data is not None

    def test_read_data_god_enabled_token_invalid(self):
        god_token = god_jwt.create()
        god_token += "INVALID"
        with RobotContext(god=True) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)
            # cause data are always only accessible  by the service itself and locally
            assert proxy.data is not None

    def test_read_data_god_disabled_token_invalid(self):
        god_token = god_jwt.create()
        god_token += "INVALID"
        with RobotContext(god=False) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)
            assert proxy.data is None

    def test_read_data_god_disabled_token_valid(self):
        god_token = god_jwt.create()
        with RobotContext(god=False) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)
            assert proxy.data is None

    def test_read_logs_god_enabled_token_valid(self):
        god_token = god_jwt.create()
        with RobotContext(god=True) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)

            assert proxy.logs == '', "when the log file doesn't exist, logs should be empty"

            for _ in range(2):
                proxy.schedule_action('start').wait()

            assert proxy.logs, "when the log file exist, logs should not be empty"

    def test_read_data_logs_god_disabled_token_valid(self):
        god_token = god_jwt.create()
        with RobotContext(god=False) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)

            for _ in range(2):
                proxy.schedule_action('start').wait()

            with self.assertRaises(RuntimeError):
                proxy.logs

    def test_read_logs_god_enabled_token_invalid(self):
        god_token = god_jwt.create()
        god_token += "INVALID"
        with RobotContext(god=True) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)

            for _ in range(2):
                proxy.schedule_action('start').wait()

            with self.assertRaises(RuntimeError):
                proxy.logs

    def test_read_data_logs_god_disabled_token_invalid(self):
        god_token = god_jwt.create()
        god_token += "INVALID"
        with RobotContext(god=False) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)

            for _ in range(2):
                proxy.schedule_action('start').wait()

            with self.assertRaises(RuntimeError):
                proxy.logs

    def test_list_services_god_disable_no_token(self):
        with RobotContext(god=False) as cl:
            proxy, service = self.create_proxy(cl)

            # creates a new instance of the client without the token
            j.clients.zrobot.get('test2', {'url': 'http://localhost:6600'})
            cl2 = ZeroRobotManager('test2')

            assert len(cl2.services.guids) == 0, "trying to list all the services without god mode disabled should not return all the existing services"
            j.clients.zrobot.delete('test2')

    def test_list_services_god_enable_no_token(self):
        with RobotContext(god=True) as cl:
            proxy, service = self.create_proxy(cl)

            # creates a new instance of the client without the token
            j.clients.zrobot.get('test2', {'url': 'http://localhost:6600'})
            cl2 = ZeroRobotManager('test2')

            assert len(cl2.services.guids) == 0, "trying to list all the services without god token should not return all the existing services"
            j.clients.zrobot.delete('test2')

    def test_list_services_god_disable_token_valid(self):
        god_token = god_jwt.create()
        with RobotContext(god=False) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)

            # creates a new instance of the client with the god token
            j.clients.zrobot.get('test2', {'url': 'http://localhost:6600'})
            cl2 = ZeroRobotManager('test2')
            cl2._client.god_token_set(god_token)

            assert len(cl2.services.guids) == 0, "trying to list all the services with god mode disabled and valid god token should not return all the existing services"
            j.clients.zrobot.delete('test2')

    def test_list_services_god_enable_token_valid(self):
        god_token = god_jwt.create()
        with RobotContext(god=True) as cl:
            cl._client.god_token_set(god_token)
            proxy, service = self.create_proxy(cl)

            # creates a new instance of the client with the god token
            j.clients.zrobot.get('test2', {'url': 'http://localhost:6600'})
            cl2 = ZeroRobotManager('test2')
            cl2._client.god_token_set(god_token)

            assert len(cl2.services.guids) == 1, "trying to list all the services without god mode enabled and god token should not return all the existing services"
            service = cl2.services.find()[0]
            assert service.data is not None, "with god mode and god token any the client should be able to read the data of any service"

            j.clients.zrobot.delete('test2')
