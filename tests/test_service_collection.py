import unittest

from zerorobot import service_collection as scol
from zerorobot.template_uid import TemplateUID


class FakeService:

    def __init__(self, guid, name):
        self.name = name
        self.guid = guid
        self.template_uid = TemplateUID.parse('github.com/jumpscale/0-robot/fakeservice/0.0.1')


class FakeService2:

    def __init__(self, guid, name):
        self.name = name
        self.guid = guid
        self.template_uid = TemplateUID.parse('github.com/jumpscale/0-robot/other/0.0.1')


class TestServiceCollection(unittest.TestCase):

    def tearDown(self):
        scol.drop_all()

    def test_add_get_service(self):
        service = FakeService('1234567890', 's1')
        scol.add(service)

        self.assertEqual(service, scol.get_by_guid('1234567890'))
        self.assertEqual(service, scol.get_by_name('s1'))
        self.assertEqual(service, scol.find(name='s1')[0])

        with self.assertRaises(scol.ServiceNotFoundError):
            scol.get_by_name("nan")

    def test_service_overwrite(self):
        s1 = FakeService('1111', 's1')
        s2 = FakeService('1111', 's2')
        s3 = FakeService('2222', 's1')
        scol.add(s1)

        with self.assertRaises(scol.ServiceConflictError, msg='should raise exception is try to overwrite service'):
            scol.add(s2)
            scol.add(s3)

    def test_list_services(self):
        services = scol.list_services()
        self.assertEqual(len(services), 0, "services count should be 0")

        s1 = FakeService('1111', 's1')
        s2 = FakeService('2222', 's2')
        s3 = FakeService('3333', 's3')
        scol.add(s1)
        scol.add(s2)

        services = scol.list_services()
        self.assertEqual(len(services), 2, "services count should be 2")
        self.assertIn(s1, services, 'service s1 should be in the returned service list')
        self.assertIn(s2, services, 'service s2 should be in the returned service list')
        self.assertNotIn(s3, services, 'service s3 should not be in the returned service list')

    def test_search_services(self):
        s1 = FakeService('1111', 's1')
        s2 = FakeService('2222', 's2')
        s3 = FakeService2('3333', 's3')
        scol.add(s1)
        scol.add(s2)
        scol.add(s3)

        results = scol.find(template_uid='github.com/jumpscale/0-robot/fakeservice/0.0.1')
        self.assertEqual(len(results), 2)
        guids = [s1.guid, s2.guid]
        for s in results:
            self.assertIn(s.guid, guids)
