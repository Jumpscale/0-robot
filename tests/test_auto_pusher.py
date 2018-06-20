import unittest

from zerorobot.config import auto_pusher


class TestAutoPusher(unittest.TestCase):

    def setup(self):
        pass

    def test_is_ssh_remote(self):
        tt = [
            {
                'url': 'https://github.com/zero-os/0-robot.git',
                'expected': False,
                'name': 'https url',
            },
            {
                'url': 'git@github.com:zero-os/0-robot.git',
                'expected': True,
                'name': 'valid',
            },
            {
                'url': 'ssh://git@docs.greenitglobe.com:10022/Threefold/it_env_zrobot_nodes-0001.git',
                'expected': True,
                'name': 'valid',
            },
        ]

        for tc in tt:
            result = auto_pusher._is_ssh_remote(tc['url'])
            self.assertEqual(result, tc['expected'], tc['name'])
