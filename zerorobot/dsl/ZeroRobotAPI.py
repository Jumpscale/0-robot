"""
This module expose the high level API that is meant to be used by service developer in the template actions.

It provie ways to create and list services from a group of ZeroRobots in a unified way.
"""

from js9 import j
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot.dsl.ZeroRobotManager import ZeroRobotManager
from zerorobot.template_uid import TemplateUID


class TemplateNotFoundError(Exception):
    """
    This exception is raised when trying to create a service
    from a template that doesn't exists
    """
    pass


class ServicesMgr:

    def __init__(self, base):
        self._base = base

    @property
    def names(self):
        """
        Return a dictionnary that contains all the service present on all
        the accessible ZeroRobots

        key is the name of the service
        value is a Service or ServiceProxy object
        """
        services = {}
        for robot in self._base.robots.values():
            services.update(robot.services.names)
        # TODO: handle naming conflict between robots
        by_name = {s.name: s for s in scol.list_services()}
        services.update(by_name)
        return services

    @property
    def guids(self):
        """
        Return a dictionnary that contains all the service present on all
        the accessible ZeroRobot

        key is the guid of the service
        value is a Service or ServiceProxy object
        """
        services = {}
        for robot in self._base.robots.values():
            services.update(robot.services.guids)
        # TODO: handle guid conflict between robots
        services.update(scol._guid_index)
        return services

    def find(self, parent=None, **kwargs):
        """
        Search for services and filter results from kwargs.
        You can filter on:
        "name", "template_uid", "template_host", "template_account", "template_repo", "template_name", "template_version"

        example: to list all services with name foo: find(name='foo')
        """
        services = {}
        for robot in self._base.robots.values():
            for service in robot.services.find(**kwargs):
                if parent and (service.parent is None or service.parent.guid != parent.guid):
                    continue
                services[service.guid] = service

        for service in scol.find(**kwargs):
            if parent and (service.parent is None or service.parent.guid != parent.guid):
                continue
            services[service.guid] = service

        return list(services.values())

    def create(self, template_uid, service_name=None, data=None):
        """
        Instantiate a service from a template
        This method first look for a ZeroRobot that manages the template_uid then create the service in the selected robots.

        If this methos is used from a service action, it first check if we can create the service in the local robot.
        If not, it looks for a remote robot to create the service onto.

        @param template_uid: UID of the template to use a base class for the service
        @param service_name: name of the service, needs to be unique within the robot instance
        @param data: a dictionnary with the data of the service to create
        @return: A Service or ServiceProxy object. depending if the service has been created locally or remotely
        """
        try:
            # we can create a service locally, the local robot has the template
            template = tcol.get(template_uid)
            return tcol.instantiate_service(template, service_name, data)
        except KeyError:
            # we need to look for a robot that handle this template
            pass

        try:
            # try to find a robot that manage the template with uid template_uid
            robot = self._base.get_robot(template_uid)
        except KeyError:
            raise TemplateNotFoundError("no robot managing the template %s found" % template_uid)

        return robot.services.create(template_uid, service_name, data)

    def upgrade(self, service_guid, template_uid):
        new_template = None

        try:
            # check if the new template is handle by the local robot
            new_template = tcol.get(template_uid)
        except KeyError:
            # we need to look for a robot that handle this template
            pass

        try:
            service = scol.get_by_guid(service_guid)
            if new_template:
                # both service and template are available locally, we can upgrade
                return scol.upgrade(service, new_template)
        except KeyError:
            # service is not local, need to do an API call
            pass

        try:
            # try to find a robot that manage the template with uid template_uid
            robot = self._base.get_robot(template_uid)
            return robot.services.upgrade(service_guid, template_uid)
        except KeyError:
            raise TemplateNotFoundError("no robot managing the template %s found" % template_uid)


class ZeroRobotAPI:
    # TODO: find better name

    def __init__(self):
        self._config_mgr = ConfigMgr()
        self.services = ServicesMgr(self)

    @property
    def robots(self):
        """
        list all the ZeroRobot accessible
        return a dictionary with
        key = url of the API of the robot
        value: ZeroRobotClient object
        """
        robots = {}
        for instance in self._config_mgr.list():
            robots[instance] = ZeroRobotManager(instance)
        return robots

    def get_robot(self, template_uid):
        """
        returns a instance of ZeroRobotClient that is managing the template identified by template_uid

        It looks into all the know ZeroRobots which one manages the template_uid and return a client to it.
        If not known robots managed the template_uid, then KeyError is raised
        """
        if isinstance(template_uid, str):
            template_uid = TemplateUID.parse(template_uid)

        def compare(a, b):
            if a.host and b.host and (a.host != b.host):
                return False
            if a.account and b.account and (a.account != b.account):
                return False
            if a.repo and b.repo and (a.repo != b.repo):
                return False
            if a.name and b.name and (a.name != b.name):
                return False
            if a.version and b.version and (a.version != b.version):
                return False
            return True

        for robot in self.robots.values():
            for uid in robot.templates.uids:
                if compare(template_uid, uid):
                    return robot
        raise KeyError("no robot that managed %s found" % template_uid)


class ConfigMgr():
    """
    Small class that abstract configmanager
    """

    location = 'j.clients.zrobot'

    def __init__(self):
        j.tools.configmanager.interactive = False

    def list(self):
        """
        list all the available zerorobot client configured

        @return: a list of instance name
        """
        return j.tools.configmanager.list(self.location)

    def set(self, instance, base_url):
        """
        create a new config

        @param instance: instance name
        @param base_url: base_url of the client
        """
        config = {'url': base_url}
        cfg = j.tools.configmanager.js9_obj_get(self.location, instance, data=config).config
        # make sure it exists on disk
        cfg.save()
        return cfg

    def delete(self, instance):
        """
        deletes a config
        @param instance: instance name
        """
        if instance not in self.list():
            return
        j.clients.zrobot.delete(instance)
