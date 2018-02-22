import os
import tempfile
import unittest
import shutil

from js9 import j
from zerorobot import service_collection as scol
from zerorobot.service_collection import BadTemplateError
from zerorobot import template_collection as tcol
from zerorobot.template.base import (ActionNotFoundError,
                                     BadActionArgumentError, TemplateBase)
from zerorobot.template_collection import _load_template
from zerorobot import config


class TestServiceTemplate(unittest.TestCase):

    def setUp(self):
        config.DATA_DIR = tempfile.mkdtemp(prefix='0robottest')
        scol.drop_all()

    def tearDown(self):
        if os.path.exists(config.DATA_DIR):
            shutil.rmtree(config.DATA_DIR)

    def load_template(self, name):
        """
        name of the template to load from the
        fixtures/templates folder
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        tmpl = _load_template("https://github.com/jumpscale/0-robot",
                              os.path.join(dir_path, 'fixtures', 'templates', name))
        return tmpl

    def test_instantiate_service(self):
        Node = self.load_template('node')
        srv = tcol.instantiate_service(Node, 'testnode')
        self.assertIsNotNone(srv, "service should not be None")
        self.assertEqual(srv.name, 'testnode', "service name should be 'testnode'")
        self.assertIsNotNone(srv.guid, "service guid should not be None")
        self.assertEqual(srv.version, Node.version, "service and template version should match")
        self.assertIsNotNone(srv.data, "service data should not be None")
        self.assertIsNotNone(srv.state, "service state should not be None")
        self.assertIsNotNone(srv.task_list, "service task_list should not be None")
        self.assertIsNotNone(srv.gl_mgr, "service greenlet manager should not be None")

    def test_instantiate_service_without_name(self):
        Node = self.load_template('node')
        srv = tcol.instantiate_service(Node)
        self.assertIsNotNone(srv, "service should not be None")
        self.assertEqual(srv.name, srv.guid, "service name should be the same as guid when created without name")
        self.assertIsNotNone(srv.guid, "service guid should not be None")
        self.assertEqual(srv.version, Node.version, "service and template version should match")
        self.assertIsNotNone(srv.data, "service data should not be None")
        self.assertIsNotNone(srv.state, "service state should not be None")
        self.assertIsNotNone(srv.task_list, "service task_list should not be None")
        self.assertIsNotNone(srv.gl_mgr, "service greenlet manager should not be None")

    def test_service_save_delete(self):
        Node = self.load_template('node')
        srv = tcol.instantiate_service(Node, 'testnode')

        srv.save()
        srv_dir = os.path.join(
            config.DATA_DIR,
            srv.template_uid.host,
            srv.template_uid.account,
            srv.template_uid.repo,
            srv.template_uid.name,
            srv.name,
            srv.guid
        )

        self.assertTrue(os.path.exists(srv_dir), "directory of the saved service should exists")
        for x in ['service.yaml', 'data.yaml', 'state.yaml']:
            self.assertTrue(os.path.exists(os.path.join(srv_dir, x)), "%s file service should exists" % x)

        service_info = j.data.serializer.yaml.load(os.path.join(srv_dir, 'service.yaml'))
        for k in ['template', 'guid', 'name', 'version']:
            self.assertTrue(k in service_info, "%s should be present in service.yaml" % k)

        srv.delete()
        self.assertFalse(os.path.exists(srv_dir), "directory of the saved service not should exists anymore")
        with self.assertRaises(scol.ServiceNotFoundError, message='service should not be found in memory anymore'):
            scol.get_by_guid(srv.guid)

    def test_service_load(self):
        Node = self.load_template('node')
        srv = tcol.instantiate_service(Node, 'testnode')
        path = srv.save()

        # unload service from memory
        scol.drop_all()

        loaded = scol.load(Node, path)
        self.assertEqual(srv.name, loaded.name, "name of the loaded service should be %s" % srv.name)
        self.assertEqual(srv.template_name, loaded.template_name, "template_name of the loaded service should be %s" % srv.template_name)
        self.assertEqual(srv.guid, loaded.guid, "guid of the loaded service should be %s" % srv.guid)
        self.assertEqual(srv.version, loaded.version, "version of the loaded service should be %s" % srv.version)
        self.assertIsNotNone(srv.data, "loaded service data should not be None")
        self.assertIsNotNone(srv.state, "loaded service state should not be None")
        self.assertIsNotNone(srv.task_list, "loaded service task_list should not be None")

    def test_service_load_dir_not_exists(self):
        Node = self.load_template('node')
        srv = tcol.instantiate_service(Node, 'testnode')
        path = srv.save()
        with self.assertRaises(FileNotFoundError):
            scol.load(Node, '/tmp/zerorobot-test-not-exists')

    def test_service_load_wrong_name(self):
        Node = self.load_template('node')
        srv = tcol.instantiate_service(Node, 'testnode')
        path = srv.save()
        # rename the folder where the service have been saved
        new_path = os.path.join(os.path.dirname(path), 'other')
        os.rename(path, new_path)
        with self.assertRaises(BadTemplateError):
            scol.load(Node, new_path)

    def test_service_load_wrong_template(self):
        Node = self.load_template('node')
        Vm = self.load_template('vm')
        srv = tcol.instantiate_service(Node, 'testnode')
        path = srv.save()
        with self.assertRaises(BadTemplateError):
            # Try to load with the wrong template class
            scol.load(Vm, path)

    def test_service_add_task(self):
        Node = self.load_template('node')
        srv = tcol.instantiate_service(Node, 'testnode')
        task = srv.schedule_action('start')
        self.assertEqual(task.action_name, 'start', "action name should be start")
        self.assertIsNotNone(task.guid, "task guid should not be None")

        task = srv.schedule_action('foo', args={'bar': 'foo'})
        self.assertDictEqual(task._args, {'bar': 'foo'})
        task.wait()
        assert task.duration != None and task.duration > 0

        self.assertEqual(task.result, 'result', "result of the task should be available in the task object")

        with self.assertRaises(ActionNotFoundError):
            srv.schedule_action('nonexist')

        with self.assertRaises(ActionNotFoundError, msg='should raise when trying to schedule a attribute that is not callable'):
            srv.schedule_action('guid')

        with self.assertRaises(BadActionArgumentError, msg='should raise BadActionArgumentError when mandatory parameters is missing'):
            task = srv.schedule_action('foo', args={'bor': 'foo'})

        with self.assertRaises(BadActionArgumentError, msg="should raise if passing argument that are not part of the signature of the action") as err:
            srv.schedule_action('foo', args={'bar': 'foo', 'wrong_arg': 'bar'})
        assert err.exception.args[0] == 'arguments "wrong_arg" are not present in the signature of the action'

    def test_update_secure(self):
        Node = self.load_template('node')
        srv = tcol.instantiate_service(Node, 'testnode')
        self.assertEqual(srv.data['ip'], '')

        with self.assertRaises(ValueError, message='should raise value error when trying to update data with a non dict object'):
            srv.data.update_secure(data='string')

        task = srv.data.update_secure(data={'ip': '127.0.0.1'})
        task.wait()
        self.assertEqual(task.action_name, 'update_data')
        self.assertEqual(srv.data['ip'], '127.0.0.1')

    def test_recurring(self):
        tmpl = self.load_template('recurring')
        srv = tmpl('foo')
        gl = srv.gl_mgr.get('recurring_monitor')
        self.assertTrue(gl.started)
