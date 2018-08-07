from gevent import monkey
# need to patch sockets to make requests async
monkey.patch_all(subprocess=False)

import os
import tempfile
import unittest

from jumpscale import j

from zerorobot.robot import Robot
from zerorobot import config
from zerorobot.git import url as giturl


class TestRobot(unittest.TestCase):

    def setUp(self):
        config.data_repo = None

    def test_add_data_repo(self):
        robot = Robot()
        dir_path = j.sal.fs.getTmpDirPath()
        robot.set_data_repo(dir_path)
        self.assertEqual(config.data_repo.path, os.path.join(dir_path, 'zrobot_data'))
        self.assertEqual(robot.data_repo_url, dir_path)

    def test_data_dir_required(self):
        with self.assertRaises(RuntimeError, msg="robot should not start if not data dir set"):
            robot = Robot()
            robot.start(testing=True)

    def test_address(self):
        robot = Robot()
        self.assertIsNone(robot.address)
        with tempfile.TemporaryDirectory() as data_dir:
            robot.set_data_repo(data_dir)
            robot.start(listen="localhost:6600", block=False)
            self.assertEqual(robot.address, ('127.0.0.1', 6600))
            robot.stop(timeout=1)
        self.assertIsNone(robot.address)

    def test_template_url(self):
        tt = (
            {
                'url': 'http://github.com/threefoldtech/0-templates',
                'repo': 'http://github.com/threefoldtech/0-templates',
                'branch': None,
                'exception': None,
            },
            {
                'url': 'http://github.com/threefoldtech/0-templates#anotherbranch',
                'repo': 'http://github.com/threefoldtech/0-templates',
                'branch': 'anotherbranch',
                'exception': None,
            },
            {
                'url': 'git@github:openvcloud/0-templates.git',
                'repo': 'git@github:openvcloud/0-templates.git',
                'branch': None,
                'exception': None,
            },
            {
                'url': 'git@github:openvcloud/0-templates.git#branch',
                'repo': 'git@github:openvcloud/0-templates.git',
                'branch': 'branch',
                'exception': None,
            },
            {
                'url': 'ssh://git@docs.greenitglobe.com:10022/account/repo.git',
                'repo': 'ssh://git@docs.greenitglobe.com:10022/account/repo.git',
                'branch': None,
                'exception': None,
            },
        )

        for test in tt:
            with self.subTest(test['url']):
                if test['exception']:
                    with self.assertRaises(test['exception'], message='mal formatted url should raise ValueError'):
                        repo, branch = giturl.parse_template_repo_url(test['url'])
                else:
                    repo, branch = giturl.parse_template_repo_url(test['url'])
                    assert repo == test['repo']
                    assert branch == test['branch']
