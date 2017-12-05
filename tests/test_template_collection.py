import unittest
import os

from zerorobot import template_collection as tcol
from zerorobot.template_collection import TemplateUID


class TestTemplateCollection(unittest.TestCase):

    def setUp(self):
        tcol._templates = {}

    def test_load_template(self):
        # valid template
        file_path = os.path.join(os.path.dirname(__file__), 'fixtures/templates/node')
        tcol._load_template("https://github.com/jumpscale/zerorobot", file_path)
        self.assertEqual(len(tcol._templates), 1, 'should have loaded a template')

        # non existing template
        with self.assertRaises(Exception, msg='loading non existing template should fail'):
            tcol._load_template("/not/existing/path")

    def test_get_template(self):
        dir_path = os.path.join(os.path.dirname(__file__), 'fixtures/templates/node')
        tcol._load_template("https://github.com/jumpscale/zerorobot", dir_path)
        self.assertGreater(len(tcol._templates), 0, 'should have loaded template, actual loaded')

        template = tcol.get('github.com/jumpscale/zerorobot/node/0.0.1')
        self.assertTrue(template is not None)
        self.assertEqual(template.template_dir, dir_path)

        with self.assertRaises(KeyError, msg="should raise KeyError"):
            tcol.get('github.com/jumpscale/zerorobot/noexists/0.0.1')

        with self.assertRaises(ValueError, msg="should raise ValueError cause template uid format is not valid"):
            tcol.get('wrong_format')

    def test_list_template(self):
        # valid template
        file_path = os.path.join(os.path.dirname(__file__), 'fixtures/templates/node')
        tcol._load_template("https://github.com/jumpscale/zerorobot", file_path)

        templates = tcol.list_templates()
        self.assertEqual(len(templates), 1, "size of templates list should 1")
        tmpl = templates[0]
        self.assertEqual(tmpl.template_name, "node")

    def test_template_uid_parsing(self):
        tt = [
            {
                'uid': 'https://github.com/account/repository/name/version',
                'error': False,
                'expected': ('github.com', 'account', 'repository', 'name', 'version'),
                'name': 'valid',
            },
            {
                'uid': 'github.com/account/repository/name/version',
                'error': False,
                'expected': ('github.com', 'account', 'repository', 'name', 'version'),
                'name': 'no scheme',
            },
            {
                'uid': 'account/repository/name/version',
                'error': True,
                'name': 'missing host',
            },
            {
                'uid': 'github.com/repository/name/version',
                'error': True,
                'name': 'no account',
            },
            {
                'uid': 'github.com/account/name/version',
                'error': True,
                'name': 'no repository',
            },
            {
                'uid': 'github.com/account/repository/version',
                'error': True,
                'name': 'missing name',
            },
            {
                'uid': 'github.com/account/repository/name',
                'error': True,
                'name': 'missing version',
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
            uid1 <= uid5
            uid1 >= uid5
            uid1 > uid5
