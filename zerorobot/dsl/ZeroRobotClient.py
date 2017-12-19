"""
This module contains a wrapper of the go-raml generated client for ZeroRobot.

Jumpscale provie a factory that return a instance of the class defined in this module
We keep this logic in this repository itself and not jumpscale so we don't spread the code over multiple repositories.
"""

from requests.exceptions import HTTPError

from zerorobot.client import Client
from zerorobot.service_proxy import ServiceProxy
from zerorobot.service_collection import ServiceConflictError


class TemplateNotFoundError(Exception):
    """
    This exception is raised when trying to create a service
    from a template that doesn't exists
    """
    pass


class ServicesMgr:

    def __init__(self, robot):
        self._robot = robot
        self._client = robot._client

    def _instantiate(self, data):
        srv = ServiceProxy(data.name, data.guid, self._client)
        srv.template_uid = data.template
        if data.parent:
            srv.parent = self._get(data.parent)
        return srv

    def _get(self, guid=None):
        resp = self._client.api.services.GetService(guid)
        return self._instantiate(resp.data)

    @property
    def names(self):
        """
        Return a dictionnary that contains all the service present on
        the ZeroRobot

        key is the name of the service
        value is a ServiceProxy object
        """
        services = {}
        resp = self._client.api.services.listServices()
        for service in resp.data:
            srv = self._instantiate(service)
            services[srv.name] = srv
        return services

    @property
    def guids(self):
        """
        Return a dictionnary that contains all the service present on
        the ZeroRobot

        key is the guid of the service
        value is a ServiceProxy object
        """
        services = {}
        resp = self._client.api.services.listServices()
        for service in resp.data:
            srv = self._instantiate(service)
            services[srv.guid] = srv
        return services

    def create(self, template_uid, service_name, data=None):
        """
        Instantiate a service from a template

        @param template_uid: UID of the template to use a base class for the service
        @param service_name: name of the service, needs to be unique within the robot instance
        @param data: a dictionnary with the data of the service to create
        """
        if template_uid not in self._robot.templates.uids:
            raise TemplateNotFoundError("template %s not found" % template_uid)

        req = {
            "template": template_uid,
            "version": "0.0.1",
            "name": service_name,
        }
        if data:
            req["data"] = data

        try:
            resp = self._client.api.services.createService(req)
        except HTTPError as err:
            if err.response.status_code == 409:
                raise ServiceConflictError(err.response.json()['message'])
            # print(err.response.json())
            raise err

        service = ServiceProxy(service_name, resp.data.guid, self._client)
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
        resp = self._client.api.templates.AddTemplateRepo(data)
        return resp.data

    @property
    def uids(self):
        """
        Returns a list of template UID present on the ZeroRobot
        """
        resp = self._client.api.templates.ListTemplates()
        return {t.uid: t for t in resp.data}


class ZeroRobotClient:

    def __init__(self, base_url):
        self._client = Client(base_url)
        self.services = ServicesMgr(self)
        self.templates = TemplatesMgr(self)
