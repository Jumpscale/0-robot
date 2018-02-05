"""
This module contains a wrapper of the go-raml generated client for ZeroRobot.

Jumpscale provie a factory that return a instance of the class defined in this module
We keep this logic in this repository itself and not jumpscale so we don't spread the code over multiple repositories.
"""

from requests.exceptions import HTTPError

from js9 import j
from zerorobot.service_collection import ServiceConflictError
from zerorobot.service_proxy import ServiceProxy
from zerorobot.template_uid import TemplateUID


class TemplateNotFoundError(Exception):
    """
    This exception is raised when trying to create a service
    from a template that doesn't exists
    """
    pass


class ServiceCreateError(Exception):
    """
    Exception raised when service fail to create
    """

    def __init__(self, msg, original_exception):
        super().__init__(msg + (": %s" % original_exception))
        self.original_exception = original_exception


class ServiceUpgradeError(Exception):
    """
    Exception raised when service fail to upgrade
    """

    def __init__(self, msg, original_exception):
        super().__init__(msg + (": %s" % original_exception))
        self.original_exception = original_exception


class ServicesMgr:

    def __init__(self, robot):
        self._robot = robot
        self._client = robot._client

    def _instantiate(self, data):
        srv = ServiceProxy(data.name, data.guid, self._client)
        srv.template_uid = TemplateUID.parse(data.template)
        if data.parent:
            srv.parent = self._get(data.parent)
        return srv

    def _get(self, guid=None):
        service, _ = self._client.api.services.GetService(guid)
        return self._instantiate(service)

    @property
    def names(self):
        """
        Return a dictionnary that contains all the service present on
        the ZeroRobot

        key is the name of the service
        value is a ServiceProxy object
        """
        results = {}
        services, _ = self._client.api.services.listServices()
        for service in services:
            srv = self._instantiate(service)
            results[srv.name] = srv
        return results

    @property
    def guids(self):
        """
        Return a dictionnary that contains all the service present on
        the ZeroRobot

        key is the guid of the service
        value is a ServiceProxy object
        """
        results = {}
        services, _ = self._client.api.services.listServices()
        for service in services:
            srv = self._instantiate(service)
            results[srv.guid] = srv
        return results

    def find(self, **kwargs):
        """
        Find some services based on some filters passed in **kwargs
        """
        results = []
        services, _ = self._client.api.services.listServices(query_params=kwargs)
        for service in services:
            results.append(self._instantiate(service))
        return results

    def create(self, template_uid, service_name=None, data=None):
        """
        Instantiate a service from a template

        @param template_uid: UID of the template to use a base class for the service
        @param service_name: name of the service, needs to be unique within the robot instance
        @param data: a dictionnary with the data of the service to create
        """
        if isinstance(template_uid, str):
            template_uid = TemplateUID.parse(template_uid)

        if template_uid not in self._robot.templates.uids:
            raise TemplateNotFoundError("template %s not found" % template_uid)

        req = {
            "template": str(template_uid),
            "version": "0.0.1",
        }
        if service_name:
            req["name"] = service_name
        if data:
            req["data"] = data

        try:
            new_service, resp = self._client.api.services.createService(req)
        except HTTPError as err:
            if err.response.status_code == 409:
                raise ServiceConflictError(err.response.json()['message'], None)
            e = err.response.json()
            raise ServiceCreateError(e['message'], err)

        service = ServiceProxy(new_service.name, new_service.guid, self._client)
        return service

    def upgrade(self, service_guid, new_template_uid):
        """
        Upgrade a service to a new version

        @param service: service guid
        @param new_template_uid: template uid to be used as new template
        """
        if isinstance(new_template_uid, str):
            new_template_uid = TemplateUID.parse(new_template_uid)

        if new_template_uid not in self._robot.templates.uids:
            raise TemplateNotFoundError("template %s not found" % new_template_uid)

        req = {"template": str(new_template_uid)}
        try:
            new_service, resp = self._client.api.services.UpgradeService(data=req, service_guid=service_guid)
        except HTTPError as err:
            e = err.response.json()
            raise ServiceUpgradeError(e['message'], err)

        service = ServiceProxy(new_service.name, new_service.guid, self._client)
        return service


class TemplatesMgr:

    def __init__(self, robot):
        self._robot = robot
        self._client = robot._client

    def add_repo(self, url, branch='master'):
        """
        Add a new template repository
        """
        data = {
            "url": url,
            "branch": branch,
        }
        repo, _ = self._client.api.templates.AddTemplateRepo(data)
        return repo

    @property
    def uids(self):
        """
        Returns a list of template UID present on the ZeroRobot
        """
        templates, _ = self._client.api.templates.ListTemplates()
        return {TemplateUID.parse(t.uid): t for t in templates}


class ZeroRobotManager:

    def __init__(self, instance='main'):
        self._client = j.clients.zrobot.get(instance)
        self.services = ServicesMgr(self)
        self.templates = TemplatesMgr(self)
