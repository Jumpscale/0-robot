# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify, request
from js9 import j
from zerorobot import service_collection as scol
from zerorobot.server import auth
from zerorobot.server.handlers.views import task_view


@auth.user.login_required
def getTaskListHandler(service_guid):
    '''
    Return all the action in the task list
    It is handler for GET /services/<service_guid>/task_list
    '''
    try:
        service = scol.get_by_guid(service_guid)
    except scol.ServiceNotFoundError:
        return jsonify(code=404, message="service with guid '%s' not found" % service_guid), 404
    # return only task waiting or all existing task for this service
    all_task = request.args.get('all')
    if all_task is not None:
        all_task = j.data.types.bool.fromString(all_task)

    tasks = [task_view(t, service) for t in service.task_list.list_tasks(all=all_task)]

    return jsonify(tasks), 200
