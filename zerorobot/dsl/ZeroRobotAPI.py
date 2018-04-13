"""
This module expose the high level API that is meant to be used by service developer in the template actions.

It provie ways to create and list services from a group of ZeroRobots in a unified way.
"""

from js9 import j
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot.dsl.ZeroRobotManager import ZeroRobotManager
from zerorobot.template_uid import TemplateUID
from zerorobot.template_collection import TemplateNotFoundError


class ServicesMgr:

    def __init__(self):
        pass

    @property
    def names(self):
        """
        Return a dictionnary that contains all the service present on the local 0-robot

        key is the name of the service
        value is a Service
        """
        services = {s.name: s for s in scol.list_services()}
        return services

    @property
    def guids(self):
        """
        Return a dictionnary that contains all the service present on the local 0-robot

        key is the guid of the service
        value is a Service
        """
        return scol._guid_index

    def find(self, **kwargs):
        """
        Search for services and filter results from kwargs.
        You can filter on:
        "name", "template_uid", "template_host", "template_account", "template_repo", "template_name", "template_version"

        example: to list all services with name foo: find(name='foo')
        """
        services = {}
        for service in scol.find(**kwargs):
            services[service.guid] = service

        return list(services.values())

    def exists(self, **kwargs):
        """
        Test if a service exists and filter results from kwargs.
        You can filter on:
        "name", "template_uid", "template_host", "template_account", "template_repo", "template_name", "template_version"
        """
        results = self.find(**kwargs)
        return len(results) > 0

    def get(self, **kwargs):
        """
        return a service service based on the filters in kwargs.
        You can filter on:
        "name", "template_uid", "template_host", "template_account", "template_repo", "template_name", "template_version"
        """
        results = self.find(**kwargs)
        i = len(results)
        if i > 1:
            raise scol.TooManyResults("%d services found" % i)
        elif i <= 0:
            raise scol.ServiceNotFoundError()
        return results[0]

    def create(self, template_uid, service_name=None, data=None):
        """
        Instantiate a service from a template on the local 0-robot

        If this methos is used from a service action, it first check if we can create the service in the local robot.
        If not, it raises TemplateNotFound error

        @param template_uid: UID of the template to use a base class for the service
        @param service_name: name of the service, needs to be unique within the robot instance
        @param data: a dictionnary with the data of the service to create
        @return: A Service object
        """
        # we can create a service locally, the local robot has the template
        template = tcol.get(template_uid)
        return tcol.instantiate_service(template, service_name, data)

    def find_or_create(self, template_uid, service_name, data):
        """
        Helper method that first check if a service exists and if not then creates it
        if the service is found, it is returned
        if the service is not found, it is created using the data passed then returned

        @param template_uid: UID of the template of the service
        @param service: the name of the service.
        @param data: a dictionnary with the data of the service if and only if the service is created
                    so if the service already exists, the data argument is not used
        """
        try:
            return self.get(template_uid=template_uid, name=service_name)
        except scol.ServiceNotFoundError:
            return self.create(template_uid=template_uid, service_name=service_name, data=data)


class TemplatesMgr:

    def __init__(self):
        pass

    def add_repo(self, url, branch='master'):
        """
        Add a new template repository

        returns the templates that were added from this repository
        """
        return tcol.add_repo(url=url, branch=branch)

    def checkout_repo(self, url, revision='master'):
        """
        Checkout a branch/tag/revision of a template repository

        @param url: url of the template repo
        @param revision: branch, tag or revision to checkout
        """
        return tcol.checkout_repo(url, revision)

    @property
    def uids(self):
        """
        Returns a dict of template UID present on the ZeroRobot
        keys are the templates uids
        values are the templates objects
        """
        return tcol._templates


class ZeroRobotAPI:
    # TODO: find better name

    def __init__(self):
        self._config_mgr = ConfigMgr()
        self.services = ServicesMgr()
        self.templates = TemplatesMgr()

    @property
    def robots(self):
        """
        list all the ZeroRobot accessible
        return a dictionary with
        key = instance name of the 0-robot
        value: ZeroRobotManager object
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
