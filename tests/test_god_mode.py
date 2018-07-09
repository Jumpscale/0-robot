# need to patch sockets to make requests async
from gevent import monkey
monkey.patch_all(subprocess=False)

import os
import shutil
import unittest
import uuid


from js9 import j
from JumpScale9.errorhandling.ErrorConditionObject import ErrorConditionObject
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
        self.robot.add_template_repo('http://github.com/zero-os/0-robot', directory='tests/fixtures/templates')
        if os.path.exists(config.data_repo.path):
            shutil.rmtree(config.data_repo.path)
        # make sure we don't have any service loaded
        scol.drop_all()
        self.robot.start(listen='127.0.0.1:6600', block=False, testing=True, god=self.god)
        return self.cl

    def __exit__(self, type, value, tb):
        self.robot.stop()
        if os.path.exists(config.data_repo.path):
            shutil.rmtree(config.data_repo.path)
        j.clients.zrobot.delete('test')


class TestServiceProxy(unittest.TestCase):

    # def start_robot(self, god):
    #     # make sure this test instance client exists
    #     j.clients.zrobot.get('test', {'url': 'http://localhost:6600'})
    #     self.cl = ZeroRobotManager('test')
    #     self.robot = Robot()
    #     self.robot.set_data_repo(j.sal.fs.getTmpDirPath())
    #     self.robot.add_template_repo('http://github.com/zero-os/0-robot', directory='tests/fixtures/templates')
    #     if os.path.exists(config.data_repo.path):
    #         shutil.rmtree(config.data_repo.path)
    #     # make sure we don't have any service loaded
    #     scol.drop_all()
    #     self.robot.start(listen='127.0.0.1:6600', block=False, testing=True, god=god)

    # def stop_robot(self):
    #     self.robot.stop()
    #     if os.path.exists(config.data_repo.path):
    #         shutil.rmtree(config.data_repo.path)
    #     j.clients.zrobot.delete('test')
    
    def create_proxy(self, client, public=False):
        template = 'github.com/zero-os/0-robot/node/0.0.1'
        name = 'node1'
        proxy = client.services.create(template, name, public=public)
        service = scol.get_by_guid(proxy.guid)
        return (proxy, service)

    def test_read_data_god_enabled_token_valid(self):
        god_token = god_jwt.create({'god_token_':'GodToken'})
        with RobotContext(god=True and god_jwt.verify(god_token)) as cl:
            proxy, service = self.create_proxy(cl)

            assert proxy.data is not None

    def test_read_data_god_enabled_token_invalid(self):
        god_token = god_jwt.create({'god_token_':'Invalid'})
        with RobotContext(god=True and god_jwt.verify(god_token)) as cl:
            proxy, service = self.create_proxy(cl)

            assert proxy.data is None

    def test_read_data_god_disabled_toekn_invalid(self):
        god_token = god_jwt.create({'god_token_':'Invalid'})
        with RobotContext(god=False and god_jwt.verify(god_token)) as cl:
            proxy, service = self.create_proxy(cl)
            assert proxy.data is None

    def test_read_data_god_disabled_token_valid(self):
        god_token = god_jwt.create({'god_token_':'GodToken'})
        with RobotContext(god=False and god_jwt.verify(god_token)) as cl:
            proxy, service = self.create_proxy(cl)
            assert proxy.data is None

    def test_read_logs_god_enabled_token_valid(self):
        god_token = god_jwt.create({'god_token_':'GodToken'})
        with RobotContext(god=True and god_jwt.verify(god_token)) as cl:
            proxy, service = self.create_proxy(cl)

            assert proxy.logs == '', "when the log file doesn't exist, logs should be empty"

            for _ in range(2):
                proxy.schedule_action('start').wait()

            assert proxy.logs, "when the log file exist, logs should not be empty"

    def test_read_data_logs_disabled_token_valid(self):
        god_token = god_jwt.create({'god_token_':'GodToken'})
        with RobotContext(god=False and god_jwt.verify(god_token)) as cl:
            proxy, service = self.create_proxy(cl)

            for _ in range(2):
                proxy.schedule_action('start').wait()

            with self.assertRaises(RuntimeError):
                proxy.logs
    def test_read_logs_god_enabled_token_invalid(self):
        god_token = god_jwt.create({'god_token_':'Invalid'})
        with RobotContext(god=True and god_jwt.verify(god_token)) as cl:
            proxy, service = self.create_proxy(cl)

            for _ in range(2):
                proxy.schedule_action('start').wait()

            with self.assertRaises(RuntimeError):
                proxy.logs

    def test_read_data_logs_disabled_token_invalid(self):
        god_token = god_jwt.create({'god_token_':'Invalid'})
        with RobotContext(god=False and god_jwt.verify(god_token)) as cl:
            proxy, service = self.create_proxy(cl)

            for _ in range(2):
                proxy.schedule_action('start').wait()

            with self.assertRaises(RuntimeError):
                proxy.logs
