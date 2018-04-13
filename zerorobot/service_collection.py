"""
this module is the only place where the service will be kept in memory.
other services and class need to use this module method to create, access, list and search the services
"""
import os

from js9 import j
from zerorobot.sqlite import SqliteIndex
from zerorobot.template_uid import TemplateUID

logger = j.logger.get('zerorobot')

_sqlite_index = SqliteIndex()
_guid_index = {}


def add(service):
    if service.guid in _guid_index:
        raise ServiceConflictError(
            message="a service with guid=%s already exist" % service.guid,
            service=_guid_index[service.guid])
    _guid_index[service.guid] = service
    _sqlite_index.add_service(service)

    logger.debug("add service %s to collection" % service)


def find(**kwargs):
    guids = _sqlite_index.find(**kwargs)
    services = [_guid_index[guid] for guid in guids]
    return services


def get_by_name(name):
    services = find(name=name)
    if len(services) > 1:
        raise TooManyResults("more then one results for service name=%s, be more precise" % name)
    if len(services) < 1:
        raise ServiceNotFoundError("service with name=%s not found" % name)
    return services[0]


def get_by_guid(guid):
    if guid not in _guid_index:
        raise ServiceNotFoundError("service with guid=%s not found" % guid)
    return _guid_index[guid]


def list_services():
    return list(_guid_index.values())


def delete(service):
    if service.guid in _guid_index:
        del _guid_index[service.guid]
    _sqlite_index.delete_service(service)

    logger.debug("delete service %s from collection" % service)


def load(template, base_path):
    """
    load the service from it's file system serialized format

    @param template: the template class to use to instantiate the service
    @param base_path: path of the directory where
                        to load the service state and data from
    """
    if not os.path.exists(base_path):
        raise FileNotFoundError("Trying to load service from %s, but directory doesn't exists" % base_path)

    guid = os.path.basename(base_path)
    service_info = j.data.serializer.yaml.load(os.path.join(base_path, 'service.yaml'))
    service_data = j.data.serializer.yaml.load(os.path.join(base_path, 'data.yaml'))

    template_uid = TemplateUID.parse(service_info['template'])
    if template_uid > template.template_uid:
        raise BadTemplateError("Trying to load service %s with template %s, while it requires %s or higher" % (guid, template.template_uid, service_info['template']))

    if service_info['guid'] != guid:
        raise BadTemplateError("Trying to load service from folder %s, but name of the service is %s"
                               % (base_path, service_info['name']))

    srv = template(name=service_info['name'], guid=service_info['guid'], data=service_data)

    srv.state.load(os.path.join(base_path, 'state.yaml'))
    srv.data.load(os.path.join(base_path, 'data.yaml'))
    srv.task_list.load(os.path.join(base_path, 'tasks.yaml'))
    srv._path = base_path
    add(srv)
    return srv


def upgrade(service, new_template, force=False):
    if not force and service.template_uid == new_template.template_uid:
        # nothing to do
        return service

    logger.info("upgrade service %s (%s) to %s", service.name, service.guid, new_template.template_uid)
    service.template_uid = new_template.template_uid

    # if there is a task running for this service, wait for it to finish, before stopping the service
    current_task = service.task_list.current
    if current_task is not None:
        current_task.wait(timeout=300)  # FIXME: fixed timeout, no timeout ?

    # stop the services
    service.gl_mgr.stop_all(wait=True)
    service.save()

    # remove service from memory
    delete(service)

    # create new instance of the service with updated version of the template
    # we use load so it loads with the same data of previous version, but with new template
    service = load(new_template, service._path)
    service.save()
    return service


def drop_all():
    """
    delete all services
    """
    for s in list_services():
        delete(s)
    _guid_index = {}


class ServiceConflictError(Exception):
    """
    Raised when trying to create a service with a duplicate name

    @param service: the conflicting service that already exists
    """

    def __init__(self, message, service):
        super().__init__(message)
        self.service = service


class TooManyResults(Exception):
    """
    Raised when trying to get a specific service and the
    search retunr more then 1 results
    """
    pass


class BadTemplateError(Exception):
    """
    Error raised when trying to load a service with a wrong template class
    """
    pass


class ServiceNotFoundError(KeyError):
    """
    Raised when trying to get a service that doesn't exists
    """
