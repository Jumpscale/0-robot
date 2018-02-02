import os
import unittest

from zerorobot import blueprint


class TestBlueprintParsing(unittest.TestCase):

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
            self.assertEqual(action['template'], 'github.com/jumpscale/0-robot/node/0.0.1')
            self.assertEqual(action['service'], 'node1')
            self.assertIn(action['action'], ['start', 'monitor'])

        self.assertEqual(len(services), 1)
        self.assertEqual(services[0]['template'], 'github.com/jumpscale/0-robot/node/0.0.1')
        self.assertEqual(services[0]['service'], 'node1')
        self.assertDictEqual(services[0]['data'], {'foo': 'bar'})

    def test_parse_with_args(self):
        content = self.read_bp('valid_with_args.bp')
        actions, services = blueprint.parse(content)

        self.assertEqual(len(actions), 1, 'number of actions should be 1')

        action = actions[0]
        self.assertEqual(action['template'], 'github.com/jumpscale/0-robot/node/0.0.1')
        self.assertEqual(action['service'], 'node1')
        self.assertIn(action['action'], 'foo')
        self.assertDictEqual(action['args'], {'bar': 'hello', 'bor': 'world'})

    def test_missing_actions(self):
        content = self.read_bp('missing_actions.bp')
        with self.assertRaises(blueprint.BadBlueprintFormatError) as cm:
            blueprint.parse(content)
        err = cm.exception
        self.assertNotEqual(err.args[0], "need to specify action key in action block")
        self.assertDictEqual(err.block, {'actions': {'template': 'github.com/jumpscale/0-robot/node/0.0.1', 'service': 'node1'}})

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

    def test_bad_template_name(self):
        content = self.read_bp('bad_template_name.bp')
        with self.assertRaises(blueprint.BadBlueprintFormatError) as cm:
            blueprint.parse(content)
        err = cm.exception
        self.assertEqual(err.args[1], "Template uid not valid")
