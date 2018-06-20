import os
from enum import Enum

from js9 import j


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


class Storage:

    def __init__(self, data_dir):
        self.webhooks = {}
        self._path = os.path.join(data_dir, 'webhooks.yml')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        if not os.path.exists(self._path):
            j.data.serializer.yaml.dump(self._path, self.webhooks)

    def add(self, url, type):
        webhook = WebHook(url, type)
        self.webhooks[webhook.id] = webhook
        self.save()
        return webhook

    def delete(self, id):
        if id in self.webhooks:
            del self.webhooks[id]
            self.save()

    def list(self, kind=None):
        if kind and isinstance(kind, str):
            kind = Kind(kind)

        for wh in self.webhooks.values():
            if kind and wh.kind != kind:
                continue
            yield wh

    def save(self):
        output = []
        for wh in self.webhooks.values():
            output.append(wh.as_dict())
        j.data.serializer.yaml.dump(self._path, output)

    def load(self):
        self.webhooks = {}
        data = j.data.serializer.yaml.load(self._path)
        for item in data:
            wb = WebHook(item['url'], Kind(item['kind']))
            self.webhooks[wb.id] = wb
