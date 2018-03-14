import os
import shutil
import tempfile
import time
import unittest
import uuid
from multiprocessing import Process

from gevent import monkey

from js9 import j
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot import config
from zerorobot.dsl.ZeroRobotAPI import TemplateNotFoundError, ZeroRobotAPI
from zerorobot.robot import Robot
from zerorobot.service_proxy import ServiceProxy
from zerorobot.template.base import TemplateBase

# need to patch sockets to make requests async
monkey.patch_all(subprocess=False)


class TestZRobotAPI(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName=methodName)
        self.api = None

    def _start_robot(self, id, with_tmpl=False):
        def new(id, with_tmpl):
            robot = Robot()
            config.DATA_DIR = tempfile.mkdtemp(prefix="robot%s" % id)
            if with_tmpl:
                robot.add_template_repo('http://github.com/jumpscale/0-robot', directory='tests/fixtures/templates')

            listen = "localhost:660%d" % int(id)
            addr = "http://%s" % listen
            robot.start(listen=listen, testing=True)
            # return robot

        addr = "http://localhost:660%d" % int(id)
        p = Process(target=new, args=(id, with_tmpl))
        p.start()
        return p, addr

    def setUp(self):
        self.previous_zrobot_cfgs = {}
        for instance in j.clients.zrobot.list():
            self.previous_zrobot_cfgs[instance] = j.clients.zrobot.get(instance)
        j.clients.zrobot.reset()

        self.api = ZeroRobotAPI()
        self.ps = []
        self.instances = []

        # start 2 robots
        for i in range(2):
            p, addr = self._start_robot(i, with_tmpl=True)
            self.ps.append(p)
            instance = "robot%d" % int(i)
            cl = j.clients.zrobot.get(instance, data={'url': addr}, create=True)
            cl.config.save()
            self.instances.append(instance)

        # give time to the robot to starts TODO: find better then sleep
        time.sleep(1)

        # make sure we don't have any service loaded
        scol.drop_all()
        # make sure we don't have any template loaded
        tcol._templates = {}

    def tearDown(self):
        for p in self.ps:
            p.terminate()
            p.join()

        for instance in self.instances:
            j.clients.zrobot.delete(instance)
        # TODO: cleanup data_dir of each robots

        # make sure we don't have any service loaded
        scol.drop_all()
        # make sure we don't have any template loaded
        tcol._templates = {}

        # restore zrobot config
        for instance, cl in self.previous_zrobot_cfgs.items():
            cl = j.clients.zrobot.get(instance, data=cl.config.data, create=True)
            cl.config.save()

    def test_robots_discovery(self):
        self.assertGreaterEqual(len(self.api.robots), 2, "should have discovered at least the 2 robots that are running for the test")
        for addr in self.instances:
            self.assertIn(addr, self.api.robots.keys())

    def test_service_create(self):
        # make sure we don't have any template loaded in the current process
        tcol._templates = {}
        with self.assertRaises(TemplateNotFoundError, msg='trying to create a service from non handled template should raise '):
            self.api.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node1')

        # load template in current process
        with tempfile.TemporaryDirectory(prefix="robotlocal") as tmpdir:
            config.DATA_DIR = tmpdir
            tcol.add_repo('http://github.com/jumpscale/0-robot', directory='tests/fixtures/templates')
            # now that we have some templates loaded, it should create a local service
            node2 = self.api.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node2')
            self.assertTrue(isinstance(node2, TemplateBase))

            # the api should get all services from the local robot only
            self.assertEqual(len(self.api.services.names), 1)
            self.assertEqual(len(self.api.services.guids), 1)
            # make sure remote robot doesn't have service created on them
            for robot in self.api.robots.values():
                self.assertEqual(len(robot.services.names), 0)

        robot = self.api.robots['robot1']
        node = robot.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node3')
        self.assertEqual(type(node), ServiceProxy, "service create on remote robot should return ServiceProxy")
        self.assertEqual(len(robot.services.guids), 1)
        # ensure we can access the remote service from the robot object
        robot.services.names[node.name]
        robot.services.guids[node.guid]

    def test_service_search(self):
        # load template in current process
        with self.subTest(name='local'):
            with tempfile.TemporaryDirectory(prefix="robotlocal") as tmpdir:
                config.DATA_DIR = tmpdir
                tcol.add_repo('http://github.com/jumpscale/0-robot', directory='tests/fixtures/templates')
                robot = self.api
                self._test_search(self.api)

        with self.subTest(name='remote'):
            self._test_search(self.api.robots['robot1'])

    def test_service_exists(self):
        # load template in current process
        with self.subTest(name='local'):
            with tempfile.TemporaryDirectory(prefix="robotlocal") as tmpdir:
                config.DATA_DIR = tmpdir
                tcol.add_repo('http://github.com/jumpscale/0-robot', directory='tests/fixtures/templates')

                self._test_exists(self.api)

        with self.subTest(name='remote'):
            self._test_exists(self.api.robots['robot1'])

    def test_service_get(self):
        with self.subTest(name='local'):
            # load template in current process
            with tempfile.TemporaryDirectory(prefix="robotlocal") as tmpdir:
                config.DATA_DIR = tmpdir
                tcol.add_repo('http://github.com/jumpscale/0-robot', directory='tests/fixtures/templates')

                self._test_get(self.api)

        with self.subTest(name='remote'):
            self._test_get(self.api.robots['robot1'])

    def test_service_find_or_create(self):
        with self.subTest(name='local'):
            # load template in current process
            with tempfile.TemporaryDirectory(prefix="robotlocal") as tmpdir:
                config.DATA_DIR = tmpdir
                tcol.add_repo('http://github.com/jumpscale/0-robot', directory='tests/fixtures/templates')

                self._test_find_or_create(self.api)

        with self.subTest(name='remote'):
            self._test_find_or_create(self.api.robots['robot1'])

    def _test_get(self, robot):
        node1 = robot.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node1')
        node2 = robot.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node2')
        vm1 = robot.services.create("github.com/jumpscale/0-robot/vm/0.0.1", 'vm1')

        self.assertEqual(node1.guid, robot.services.get(name='node1').guid)
        self.assertEqual(node2.guid, robot.services.get(name='node2').guid)
        self.assertEqual(vm1.guid, robot.services.get(name='vm1').guid)

        self.assertEqual(vm1.guid, robot.services.get(template_uid='github.com/jumpscale/0-robot/vm/0.0.1').guid)

        with self.assertRaises(scol.TooManyResults):
            robot.services.get(template_host='github.com')
        with self.assertRaises(scol.TooManyResults):
            robot.services.get(template_account='jumpscale')
        with self.assertRaises(scol.TooManyResults):
            robot.services.get(template_repo='0-robot')
        with self.assertRaises(scol.TooManyResults):
            robot.services.get(template_name='node')
        with self.assertRaises(scol.TooManyResults):
            robot.services.get(template_version='0.0.1')

        with self.assertRaises(scol.ServiceNotFoundError):
            self.assertFalse(robot.services.get(name='nan'))
        with self.assertRaises(scol.ServiceNotFoundError):
            self.assertFalse(robot.services.get(template_uid='github.com/jumpscale/0-robot/node/1.1.0'))
        with self.assertRaises(scol.ServiceNotFoundError):
            self.assertFalse(robot.services.get(template_name='other'))

    def _test_exists(self, robot):
        node1 = robot.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node1')
        node2 = robot.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node2')
        vm1 = robot.services.create("github.com/jumpscale/0-robot/vm/0.0.1", 'vm1')

        self.assertTrue(robot.services.exists(name='node1'))
        self.assertTrue(robot.services.exists(name='node2'))
        self.assertTrue(robot.services.exists(name='vm1'))

        self.assertTrue(robot.services.exists(template_uid='github.com/jumpscale/0-robot/node/0.0.1'))
        self.assertTrue(robot.services.exists(template_host='github.com'))
        self.assertTrue(robot.services.exists(template_account='jumpscale'))
        self.assertTrue(robot.services.exists(template_repo='0-robot'))
        self.assertTrue(robot.services.exists(template_name='node'))
        self.assertTrue(robot.services.exists(template_version='0.0.1'))

        self.assertFalse(robot.services.exists(name='nan'))
        self.assertFalse(robot.services.exists(template_uid='github.com/jumpscale/0-robot/node/1.1.0'))
        self.assertFalse(robot.services.exists(template_name='other'))

    def _test_search(self, robot):
        node1 = robot.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node1')
        node2 = robot.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node2')
        vm1 = robot.services.create("github.com/jumpscale/0-robot/vm/0.0.1", 'vm1')

        results = robot.services.find(template_uid="github.com/jumpscale/0-robot/node/0.0.1")
        self.assertEqual(len(results), 2)
        guids = [node1.guid, node2.guid]
        for s in results:
            self.assertIn(s.guid, guids)

        results = robot.services.find(name='node1')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].guid, node1.guid)

        results = robot.services.find(template_version='0.0.1', template_name='node')
        self.assertEqual(len(results), 2)
        guids = [node1.guid, node2.guid]
        for s in results:
            self.assertIn(s.guid, guids)

    def _test_find_or_create(self, robot):
        node1 = robot.services.create("github.com/jumpscale/0-robot/node/0.0.1", 'node1')
        assert len(robot.services.guids) == 1

        srv = robot.services.find_or_create(template_uid="github.com/jumpscale/0-robot/node/0.0.1", service_name='node1', data={})
        assert node1.guid == srv.guid, "find or create should return service if it exists"
        assert len(robot.services.guids) == 1

        srv = robot.services.find_or_create(template_uid="github.com/jumpscale/0-robot/node/0.0.1", service_name='node2', data={})
        assert node1.guid != srv.guid, "find or create should create a service if it doesn't exists"
        assert len(robot.services.guids) == 2
