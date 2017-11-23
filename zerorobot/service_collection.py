"""
this module is the only place where the service will be kept in memory.
other services and class need to use this module method to create, access, list and search the services
"""

_name_index = {}
_guid_index = {}


def add_service(service):
    if hasattr(service, 'name'):
        if service.name in _name_index:
            raise ServiceConflictError("a service with name=%s already exist" % service.name)
        _name_index[service.name] = service

    if hasattr(service, 'guid'):
        if service.guid in _name_index:
            raise ServiceConflictError("a service with guid=%s already exist" % service.guid)
        _guid_index[service.guid] = service


def get_by_name(name):
    if name not in _name_index:
        return KeyError("service with name=%s not found" % name)
    return _name_index[name]


def get_by_guid(guid):
    if guid not in _guid_index:
        return KeyError("service with guid=%s not found" % guid)
    return _guid_index[guid]


class ServiceConflictError(Exception):
    pass
