import os
import shutil
import tempfile
import unittest

from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot import blueprint, config
from zerorobot.server.handlers.ExecuteBlueprintHandler import (_instanciate_services,
                                                               _schedule_action)


class TestBlueprintParsing(unittest.TestCase):

    def setUp(self):
        config.DATA_DIR = tempfile.mkdtemp(prefix='0robottest')
        scol.drop_all()

    def tearDown(self):
        if os.path.exists(config.DATA_DIR):
            shutil.rmtree(config.DATA_DIR)

    def read_bp(self, name):
        bp_path = os.path.join(os.path.dirname(__file__), 'fixtures/blueprints/%s' % name)
        content = None
        with open(bp_path) as f:
            content = f.read()
        return content

    def test_parse_blueprint(self):
        content = self.read_bp('valid.bp')
        actions, services = blueprint.parse(content)

        self.assertEqual(len(actions), 2, 'number of actions should be 2')
        for action in actions:
            self.assertEqual(action['template'], 'github.com/zero-os/0-robot/node/0.0.1')
            self.assertEqual(action['service'], 'node1')
            self.assertIn(action['action'], ['start', 'monitor'])

        self.assertEqual(len(services), 2)
        self.assertEqual(services[0]['template'], 'github.com/zero-os/0-robot/node/0.0.1')
        self.assertEqual(services[0]['service'], 'node1')
        self.assertDictEqual(services[0]['data'], {'foo': 'bar'})

    def test_parse_with_args(self):
        content = self.read_bp('valid_with_args.bp')
        actions, services = blueprint.parse(content)

        self.assertEqual(len(actions), 1, 'number of actions should be 1')

        action = actions[0]
        self.assertEqual(action['template'], 'github.com/zero-os/0-robot/node/0.0.1')
        self.assertEqual(action['service'], 'node1')
        self.assertIn(action['action'], 'foo')
        self.assertDictEqual(action['args'], {'bar': 'hello', 'bor': 'world'})

    def test_missing_actions(self):
        content = self.read_bp('missing_actions.bp')
        with self.assertRaises(blueprint.BadBlueprintFormatError) as cm:
            blueprint.parse(content)
        err = cm.exception
        self.assertNotEqual(err.args[0], "need to specify action key in action block")
        self.assertDictEqual(err.block, {'actions': {'template': 'github.com/zero-os/0-robot/node/0.0.1', 'service': 'node1'}})

    def test_bad_service_key(self):
        content = self.read_bp('bad_service_key.bp')
        with self.assertRaises(blueprint.BadBlueprintFormatError) as cm:
            blueprint.parse(content)
        err = cm.exception
        self.assertEqual(err.args[1], "Key for service creation is not right format, needs to be '$template__$instance', found:'node_node1'")

    def test_bad_service_name(self):
        content = self.read_bp('bad_service_name.bp')
        with self.assertRaises(blueprint.BadBlueprintFormatError) as cm:
            blueprint.parse(content)
        err = cm.exception
        self.assertEqual(err.args[1], "Service name should be digits or alphanumeric. you passed [node1$bad]")


class TestBlueprintExecution(unittest.TestCase):

    def setUp(self):
        tcol.add_repo("https://github.com/zero-os/0-robot", directory='tests/fixtures/templates')
        scol.drop_all()

    def test_instanciate_service(self):
        services = [
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'name',
            },
            {
                'template': 'github.com/zero-os/0-robot/vm/0.0.1',
                'service': 'name',
            },
        ]

        for service in services:
            _instanciate_services(service)

        self.assertEqual(len(scol.list_services()), 2)
        self.assertEqual(len(scol.find(template_uid='github.com/zero-os/0-robot/node/0.0.1')), 1)
        self.assertEqual(len(scol.find(template_uid='github.com/zero-os/0-robot/vm/0.0.1')), 1)

    def test_instanciate_service_duplicate(self):
        services = [
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'name',
            },
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'name',
            },
        ]

        for service in services:
            _instanciate_services(service)

        self.assertEqual(len(scol.list_services()), 1)
        self.assertEqual(len(scol.find(template_uid='github.com/zero-os/0-robot/node/0.0.1')), 1)

    def test_schedule_actions(self):
        services = [
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'name',
            },
            {
                'template': 'github.com/zero-os/0-robot/vm/0.0.1',
                'service': 'name',
            },
        ]

        for service in services:
            _instanciate_services(service)

        actions = [
            {
                'template': 'github.com/zero-os/0-robot/node',
                'name': 'name',
                'action': 'start'
            },
        ]
        tasks = []
        for action_item in actions:
            tasks.extend(_schedule_action(action_item))

        self.assertEqual(len(tasks), 1)

    def test_schedule_actions_template_filter(self):
        services = [
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'node1',
            },
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'node2',
            },
            {
                'template': 'github.com/zero-os/0-robot/vm/0.0.1',
                'service': 'vm1',
            },
        ]

        for service in services:
            _instanciate_services(service)

        actions = [
            {
                'template': 'github.com/zero-os/0-robot/node',
                'action': 'start'
            },
        ]
        tasks = []
        for action_item in actions:
            tasks.extend(_schedule_action(action_item))

        self.assertEqual(len(tasks), 2)

    def test_schedule_actions_name_filter(self):
        services = [
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'node1',
            },
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'node2',
            },
            {
                'template': 'github.com/zero-os/0-robot/vm/0.0.1',
                'service': 'vm1',
            },
        ]

        for service in services:
            _instanciate_services(service)

        actions = [{
            'service': 'node1',
            'action': 'start'
        }]
        tasks = []
        for action_item in actions:
            tasks.extend(_schedule_action(action_item))

        self.assertEqual(len(tasks), 1)

    def test_schedule_actions_all_services(self):
        services = [
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'node1',
            },
            {
                'template': 'github.com/zero-os/0-robot/node/0.0.1',
                'service': 'node2',
            },
            {
                'template': 'github.com/zero-os/0-robot/vm/0.0.1',
                'service': 'vm1',
            },
        ]

        for service in services:
            _instanciate_services(service)

        actions = [{
            'action': 'start'
        }]
        tasks = []
        for action_item in actions:
            tasks.extend(_schedule_action(action_item))

        self.assertEqual(len(tasks), 3)
