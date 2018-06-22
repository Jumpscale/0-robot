# DO NOT EDIT THIS FILE. This file will be overwritten when re-running go-raml.

from flask import Blueprint
from . import handlers


services_api = Blueprint('services_api', __name__)


@services_api.route('/services', methods=['GET'])
def listServices():
    """
    List all the services known by the ZeroRobot.
    It is handler for GET /services
    """
    return handlers.listServicesHandler()


@services_api.route('/services', methods=['POST'])
def createService():
    """
    create a new service
    It is handler for POST /services
    """
    return handlers.createServiceHandler()


@services_api.route('/services/<service_guid>', methods=['GET'])
def GetService(service_guid):
    """
    Get the detail of a service
    It is handler for GET /services/<service_guid>
    """
    return handlers.GetServiceHandler(service_guid)


@services_api.route('/services/<service_guid>', methods=['DELETE'])
def DeleteService(service_guid):
    """
    Delete a service
    It is handler for DELETE /services/<service_guid>
    """
    return handlers.DeleteServiceHandler(service_guid)


@services_api.route('/services/<service_guid>/actions', methods=['GET'])
def ListActions(service_guid):
    """
    List all the possible action a service can do.
    It is handler for GET /services/<service_guid>/actions
    """
    return handlers.ListActionsHandler(service_guid)


@services_api.route('/services/<service_guid>/task_list', methods=['GET'])
def getTaskList(service_guid):
    """
    Return all the action in the task list
    It is handler for GET /services/<service_guid>/task_list
    """
    return handlers.getTaskListHandler(service_guid)


@services_api.route('/services/<service_guid>/task_list', methods=['POST'])
def AddTaskToList(service_guid):
    """
    Add a task to the task list
    It is handler for POST /services/<service_guid>/task_list
    """
    return handlers.AddTaskToListHandler(service_guid)


@services_api.route('/services/<service_guid>/task_list/<task_guid>', methods=['GET'])
def GetTask(task_guid, service_guid):
    """
    Retrieve the detail of a task
    It is handler for GET /services/<service_guid>/task_list/<task_guid>
    """
    return handlers.GetTaskHandler(task_guid, service_guid)


@services_api.route('/services/<service_guid>/logs', methods=['GET'])
def GetLogs(service_guid):
    """
    returns the logs of the services tasks
    It is handler for GET /services/<service_guid>/logs
    """
    return handlers.GetLogsHandler(service_guid)
