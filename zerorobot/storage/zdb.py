import os

import msgpack

from js9 import j

from .base import ServiceStorageBase, _serialize_service


class ZDBServiceStorage(ServiceStorageBase):

    def __init__(self, addr, port, admin_passwd='', encr_key=''):
        super().__init__()
        zdb = j.clients.zdb.configure(instance='zrobot',
                                      secrets='',
                                      addr=addr,
                                      port=port,
                                      adminsecret=admin_passwd or '',
                                      mode='user',
                                      encryptionkey=encr_key or '')

        self._ns = zdb.namespace_new('zrobot_data')

    def save(self, service):
        serialized_service = _serialize_service(service)
        self._ns.set(msgpack.dumps(serialized_service), service.guid)

    def list(self):
        for guid in self._ns.list():
            obj = self._ns.get(guid)
            service = msgpack.loads(obj, encoding='utf-8')
            yield service

    def delete(self, service):
        self._ns.delete(service.guid)
