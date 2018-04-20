import json
import os
import tempfile
import unittest
import pytest

from zerorobot.server.app import app
from zerorobot.template_collection import _load_template
import zerorobot.service_collection as scol
import zerorobot.template_collection as tcol


def _load_data(resp):
    bdata = resp.get_data()
    return json.loads(bdata.decode())


def _validate_content_type(resp):
    assert 'application/json' == resp.headers.get("Content-type")


def load_template(name):
    """
    name of the template to load from the
    fixtures/templates folder
    """
    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    tmpl = _load_template("https://github.com/zero-os/0-robot",
                          os.path.join('..', dir_path, 'fixtures', 'templates', name))
    return tmpl


def create_service(template, name, data=None):
    Tmpl = load_template(template)
    service = Tmpl(name=name, data=data)
    return service


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        scol.drop_all()
        tcol._templates = {}

    def tearDown(self):
        pass

    def test_list_services_empty(self):
        resp = self.app.get("/services")
        assert resp.status_code == 200
        _validate_content_type(resp)
        assert _load_data(resp) == []

    def test_add_list_services(self):
        node1 = create_service('node', 'node1')
        scol.add(node1)
        node2 = create_service('node', 'node2')
        scol.add(node2)

        resp = self.app.get("/services")
        assert resp.status_code == 200
        _validate_content_type(resp)
        data = _load_data(resp)
        assert len(data) == 2
        for s in data:
            if s['guid'] == node1.guid:
                node = node1
            elif s['guid'] == node2.guid:
                node = node2
            expected = {
                "template": node.template_uid,
                "version": node.template_uid.version,
                "name": node.name,
                "guid": node.guid
            }
            # assert partial dict
            assert s.items() >= expected.items()

    def test_add_list_services_filter(self):
        service = create_service('node', 'node1')
        scol.add(service)

        filters = ["name", "template_uid", "template_host", "template_account", "template_repo", "template_name", "template_version"]
        valid = [service.name, service.template_uid, service.template_uid.host, service.template_uid.account, service.template_uid.repo, service.template_uid.name, service.template_uid.version]

        for i in range(len(filters)):
            f = filters[i]
            val = valid[i]
            url = '/services?%s=%s' % (f, val)
            resp = self.app.get(url)
            assert resp.status_code == 200
            assert len(_load_data(resp)) == 1

        for i in range(len(filters)):
            f = filters[i]
            resp = self.app.get('/services?%s=invalid' % f)
            assert resp.status_code == 200
            assert _load_data(resp) == []

    @unittest.skip("need to adapt the test to work with authentication")
    def test_list_actions(self):
        service = create_service('node', 'node1')
        scol.add(service)
        resp = self.app.get('/services/%s/actions' % service.guid)
        _validate_content_type(resp)
        data = _load_data(resp)
        expected = sorted(["start", "stop", "foo", "delete", 'error', "update_data", 'bar', 'fookwargs'])
        actual = sorted([a['name'] for a in data])
        assert expected == actual

        resp = self.app.get('/services/notfound/actions')
        assert resp.status_code == 404


if __name__ == '__main__':
    unittest.main()
