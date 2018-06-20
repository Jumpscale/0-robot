import os
import unittest

from js9 import j
from zerorobot import webhooks


class TestWebHooks(unittest.TestCase):

    def setUp(self):
        self.storage = webhooks.Storage(j.sal.fs.getTmpDirPath())

    def tearDown(self):
        if os.path.exists(self.storage._path):
            os.remove(self.storage._path)

    def test_add_list(self):
        url = 'http://webhooks.com'
        wh = self.storage.add(url, 'eco')
        assert wh.id == j.data.hash.md5_string(url)
        assert wh.url == url
        assert wh.kind == webhooks.Kind.ECO
        assert 1 == len(list(self.storage.list()))
        assert 1 == len(list(self.storage.list(kind='eco')))
        assert wh == list(self.storage.list())[0]

        wh = self.storage.add(url, 'eco')
        assert 1 == len(list(self.storage.list())), 'adding twice the same url should not add a new entry'

        url2 = 'http://webhooks2.com'
        wh = self.storage.add(url2, 'eco')
        assert 2 == len(list(self.storage.list())), 'adding 2 different url should create 2 entries'

    def test_add_wrong_kind(self):
        with self.assertRaises(ValueError, msg='adding a new web hook should fail if the kind of web hook is not supported'):
            url = 'http://webhooks.com'
            wh = self.storage.add(url, 'notsupported')

    def test_delete(self):
        url = 'http://webhooks.com'
        wh = self.storage.add(url, 'eco')

        self.storage.delete(wh.id)

    def test_save_load(self):
        initial = []
        for i in range(10):
            url = 'http://webhooks%d.com' % i
            wh = self.storage.add(url, 'eco')
            initial.append(wh)

        self.storage.save()
        self.storage.webhooks = {}
        self.storage.load()
        assert len(initial) == len(list(self.storage.list()))
        for wha in self.storage.list():
            for whb in initial:
                if wha.id == whb.id:
                    assert wha.url == whb.url
                    assert wha.kind == whb.kind
