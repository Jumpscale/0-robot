import os
from enum import Enum

import msgpack

from jumpscale import j


class Kind(Enum):
    ECO = 'eco'


class WebHook:

    def __init__(self, url, kind):
        if isinstance(kind, str):
            kind = Kind(kind)

        if not isinstance(kind, Kind):
            raise ValueError("type should be an instance of WebHookKind, not %s" % type(kind))

        self._id = j.data.hash.md5_string(url)
        self._url = url
        self._kind = kind

    @property
    def id(self):
        return self._id

    @property
    def url(self):
        return self._url

    @property
    def kind(self):
        return self._kind

    def as_dict(self):
        return {'id': self.id, 'url': self.url, 'kind': self.kind.value}


class Manager:

    def __init__(self, store):
        self._store = store
        self.webhooks = store.load()

    def add(self, url, type):
        webhook = WebHook(url, type)
        self.webhooks[webhook.id] = webhook
        self._store.save(self.webhooks)
        return webhook

    def delete(self, id):
        if id in self.webhooks:
            del self.webhooks[id]
            self._store.save(self.webhooks)

    def list(self, kind=None):
        if kind and isinstance(kind, str):
            kind = Kind(kind)

        for wh in self.webhooks.values():
            if kind and wh.kind != kind:
                continue
            yield wh


class FSStorage:

    def __init__(self, data_dir):
        self._path = os.path.join(data_dir, 'webhooks.yml')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def save(self, webhooks):
        output = []
        for wh in webhooks.values():
            output.append(wh.as_dict())
        j.data.serializer.yaml.dump(self._path, output)

    def load(self):
        webhooks = {}
        if not os.path.exists(self._path):
            return webhooks

        data = j.data.serializer.yaml.load(self._path) or []
        for item in data:
            wb = WebHook(item['url'], Kind(item['kind']))
            webhooks[wb.id] = wb
        return webhooks


class ZDBStorage:

    def __init__(self, addr, port, admin_passwd='', encr_key=''):
        zdb = j.clients.zdb.configure(instance='zrobot',
                                      secrets='',
                                      addr=addr,
                                      port=port,
                                      adminsecret=admin_passwd or '',
                                      mode='user',
                                      encryptionkey=encr_key or '')

        self._ns = zdb.namespace_new('zrobot_webhooks')

    def save(self, webhooks):
        self._ns.set(
            msgpack.dumps([wh.as_dict() for wh in webhooks.values()]),
            'webhooks'
        )

    def load(self):
        webhooks = {}
        obj = self._ns.get('webhooks')
        if obj:
            for item in msgpack.loads(obj, encoding='utf-8'):
                wb = WebHook(item['url'], Kind(item['kind']))
                webhooks[wb.id] = wb
        return webhooks
