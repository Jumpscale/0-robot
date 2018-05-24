# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify, request

from zerorobot import service_collection as scol
from zerorobot.server.handlers.views import task_view
from zerorobot.task import TaskNotFoundError

from zerorobot.server import auth


@auth.service.login_required
def GetTaskHandler(task_guid, service_guid):
    '''
    Retrieve the detail of a task
    It is handler for GET /services/<service_guid>/task_list/<task_guid>
    '''
    try:
        service = scol.get_by_guid(service_guid)
    except scol.ServiceNotFoundError:
        return jsonify(code=404, message="service with guid '%s' not found" % service_guid), 404

    try:
        task = service.task_list.get_task_by_guid(task_guid)
    except TaskNotFoundError:
        return jsonify(code=404, message="task with guid '%s' not found" % task_guid), 404

    return jsonify(task_view(task, service)), 200
