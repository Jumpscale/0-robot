from urllib.parse import urlparse, parse_qs

from flask import request
from flask.helpers import make_response
from prometheus_client import core, generate_latest, CONTENT_TYPE_LATEST

from .host import monitor_host_metrics
from .robot import monitor_robot_metrics


def monitor(app):
    monitor_host_metrics()
    monitor_robot_metrics()
    app.add_url_rule('/metrics', 'prometheus_metrics', view_func=metrics)


def metrics():
    registry = core.REGISTRY
    params = parse_qs(urlparse(request.path).query)
    if 'name[]' in params:
        registry = registry.restricted_registry(params['name[]'])
    output = generate_latest(registry)
    response = make_response(output)
    response.headers['Content-Type'] = CONTENT_TYPE_LATEST
    return response
