import os
import unittest

from zerorobot import template_collection as tcol
from zerorobot.git import url as giturl
from zerorobot.template_collection import TemplateNotFoundError
from zerorobot.template_uid import TemplateUID


class TestTemplateCollection(unittest.TestCase):

    def setUp(self):
        tcol._templates = {}

    def test_load_template(self):
        # valid template
        file_path = os.path.join(os.path.dirname(__file__), 'fixtures/templates/node')
        tcol._load_template("https://github.com/zero-os/0-robot", file_path)
        self.assertEqual(len(tcol._templates), 1, 'should have loaded a template')

        # non existing template
        with self.assertRaises(Exception, msg='loading non existing template should fail'):
            tcol._load_template("/not/existing/path", file_path)

    def test_get_template(self):
        dir_path = os.path.join(os.path.dirname(__file__), 'fixtures/templates/node')
        tcol._load_template("https://github.com/zero-os/0-robot", dir_path)
        self.assertGreater(len(tcol._templates), 0, 'should have loaded template, actual loaded')

        template = tcol.get('github.com/zero-os/0-robot/node/0.0.1')
        self.assertTrue(template is not None)
        self.assertEqual(template.template_dir, dir_path)

        with self.assertRaises(TemplateNotFoundError, msg="should raise TemplateNotFoundError"):
            tcol.get('github.com/zero-os/0-robot/noexists/0.0.1')

    def test_list_template(self):
        # valid template
        file_path = os.path.join(os.path.dirname(__file__), 'fixtures/templates/node')
        tcol._load_template("https://github.com/zero-os/0-robot", file_path)

        templates = tcol.list_templates()
        self.assertEqual(len(templates), 1, "size of templates list should 1")
        tmpl = templates[0]
        self.assertEqual(tmpl.template_name, "node")

    def test_template_uid_parsing(self):
        tt = [
            {
                'uid': 'github.com/account/repository/name/0.0.1',
                'error': False,
                'expected': ('github.com', 'account', 'repository', 'name', '0.0.1'),
                'name': 'valid',
            },
            {
                'uid': 'github.com/account/repository/name/0.0.1',
                'error': False,
                'expected': ('github.com', 'account', 'repository', 'name', '0.0.1'),
                'name': 'no scheme',
            },
            {
                'uid': 'account/repository/name/0.0.1',
                'error': True,
                'name': 'missing host',
            },
            {
                'uid': 'github.com/repository/name/0.0.1',
                'error': True,
                'name': 'no account',
            },
            {
                'uid': 'github.com/account/name/0.0.1',
                'error': True,
                'name': 'no repository',
            },
            {
                'uid': 'github.com/account/repository/0.0.1',
                'error': True,
                'name': 'missing name',
            },
            {
                'uid': 'github.com/account/repository/name',
                'error': False,
                'expected': ('github.com', 'account', 'repository', 'name'),
                'name': 'missing version',
            },
            {
                'uid': 'name/0.0.1',
                'error': False,
                'expected': ('name', '0.0.1'),
                'name': 'name and 0.0.1',
            },
            {
                'uid': 'name',
                'error': False,
                'expected': ('name',),
                'name': 'just name',
            }

        ]

        for tc in tt:
            if tc['error'] is False:
                uid = TemplateUID.parse(tc['uid'])
                self.assertEqual(uid.tuple(), tc['expected'], tc['name'])
            else:
                with self.assertRaises(ValueError, msg=tc['name']):
                    uid = TemplateUID.parse(tc['uid'])

    def test_template_uid_comparaison(self):
        uid1 = TemplateUID.parse('github.com/account/repository/name/1.0.0')
        uid2 = TemplateUID.parse('github.com/account/repository/name/1.0.0')
        uid3 = TemplateUID.parse('github.com/account/repository/name/1.0.1')
        uid4 = TemplateUID.parse('github.com/account/repository/name/0.9.1')
        uid5 = TemplateUID.parse('github.com/account/repository/other/1.0.0')

        self.assertTrue(uid1 == uid2)
        self.assertTrue(uid1 != uid3)
        self.assertTrue(uid1 < uid3)
        self.assertTrue(uid1 <= uid3)
        self.assertTrue(uid1 > uid4)
        self.assertTrue(uid1 >= uid4)

        with self.assertRaises(ValueError, msg="should not compare 2 different template"):
            uid1 < uid5
        with self.assertRaises(ValueError, msg="should not compare 2 different template"):
            uid1 <= uid5
        with self.assertRaises(ValueError, msg="should not compare 2 different template"):
            uid1 >= uid5
        with self.assertRaises(ValueError, msg="should not compare 2 different template"):
            uid1 > uid5

    def test_parse_git_url(self):
        tb = [
            {
                'url': 'git@hostname:account/repo',
                'protocol': 'git',
                'host': 'hostname',
                'account': 'account',
                'repo': 'repo',
                'valid': True
            },
            {
                'url': 'https://hostname/account/repo',
                'protocol': 'https',
                'host': 'hostname',
                'account': 'account',
                'repo': 'repo',
                'valid': True
            },
            {
                # https://github.com/zero-os/0-robot/issues/69
                'url': 'ssh://git@docs.greenitgloe.com:10022/Threefold/it_env_zrobot_nodes-0001.git',
                'protocol': 'git',
                'host': 'docs.greenitgloe.com',
                'account': 'Threefold',
                'repo': 'it_env_zrobot_nodes-0001',
                'valid': True
            }
        ]

        for test in tb:
            if test['valid']:
                protocol, host, account, repo = giturl.parse(test['url'])
                self.assertEqual(protocol, test['protocol'])
                self.assertEqual(host, test['host'])
                self.assertEqual(account, test['account'])
                self.assertEqual(repo, test['repo'])
            else:
                with self.assertRaises(RuntimeError):
                    giturl.parse(test['url'])

    def test_find(self):
        assert tcol.find() == [], "find should return an empty list when there are no templates loaded"

        # load some templates
        dir_path = os.path.join(os.path.dirname(__file__), 'fixtures/templates/node')
        tcol._load_template("https://github.com/zero-os/0-robot", dir_path)

        assert tcol.find() != [], "find should not return an empty list when there are some templates loaded"
        assert len(tcol.find()) == len(tcol.list_templates()), "find without argument should return the full list of loaded templates"

        assert len(tcol.find(host='github.com')) != 0
        assert len(tcol.find(host='gitlab.com')) == 0

        assert len(tcol.find(account='zero-os')) != 0
        assert len(tcol.find(account='nonexisting')) == 0

        assert len(tcol.find(repo='0-robot')) != 0
        assert len(tcol.find(repo='nonexisting')) == 0

        assert len(tcol.find(name='node')) == 1
        assert len(tcol.find(name='nonexisting')) == 0

        assert len(tcol.find(version='0.0.1')) != 0
        assert len(tcol.find(version='nonexisting')) == 0

        found = tcol.find(host='github.com', account='zero-os', repo='0-robot', name='node', version='0.0.1')
        assert len(found) == 1
        assert str(found[0].template_uid) == 'github.com/zero-os/0-robot/node/0.0.1'
