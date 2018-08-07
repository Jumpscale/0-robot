import os
import unittest

from jumpscale import j
from zerorobot import webhooks


class TestWebHooks(unittest.TestCase):

    def setUp(self):
        self.manager = webhooks.Manager(webhooks.FSStorage(j.sal.fs.getTmpDirPath()))

    def tearDown(self):
        if os.path.exists(self.manager._store._path):
            os.remove(self.manager._store._path)

    def test_add_list(self):
        url = 'http://webhooks.com'
        wh = self.manager.add(url, 'eco')
        assert wh.id == j.data.hash.md5_string(url)
        assert wh.url == url
        assert wh.kind == webhooks.webhooks.Kind.ECO
        assert 1 == len(list(self.manager.list()))
        assert 1 == len(list(self.manager.list(kind='eco')))
        assert wh == list(self.manager.list())[0]

        wh = self.manager.add(url, 'eco')
        assert 1 == len(list(self.manager.list())), 'adding twice the same url should not add a new entry'

        url2 = 'http://webhooks2.com'
        wh = self.manager.add(url2, 'eco')
        assert 2 == len(list(self.manager.list())), 'adding 2 different url should create 2 entries'

    def test_add_wrong_kind(self):
        with self.assertRaises(ValueError, msg='adding a new web hook should fail if the kind of web hook is not supported'):
            url = 'http://webhooks.com'
            wh = self.manager.add(url, 'notsupported')

    def test_delete(self):
        url = 'http://webhooks.com'
        wh = self.manager.add(url, 'eco')

        self.manager.delete(wh.id)

    def test_save_load(self):
        initial = []
        for i in range(10):
            url = 'http://webhooks%d.com' % i
            wh = self.manager.add(url, 'eco')
            initial.append(wh)

        self.manager.webhooks = {}
        self.manager.webhooks = self.manager._store.load()
        assert len(initial) == len(list(self.manager.list()))
        for wha in self.manager.list():
            for whb in initial:
                if wha.id == whb.id:
                    assert wha.url == whb.url
                    assert wha.kind == whb.kind

    def test_load_empty_file(self):
        if not os.path.exists(self.manager._store._path):
            open(self.manager._store._path, 'w+').close()
        os.truncate(self.manager._store._path, 0)
        self.manager._store.load()
