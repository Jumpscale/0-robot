# THIS FILE IS SAFE TO EDIT. It will not be overwritten when rerunning go-raml.

from flask import jsonify, request
from zerorobot import service_collection as scol
from zerorobot.prometheus.host.linux import cpu_stat, mem_stat


def GetMetricsHandler():
    mem_active, mem_total, mem_cached, mem_free, swap_total, swap_free = mem_stat.mem_stats()
    output = {
        'cpu': cpu_stat.cpu_percents(),
        'memory': {
            'total': mem_total,
            'active': mem_active,
            'free': mem_free,
            'cached': mem_cached,
            'swap_total': swap_total,
            'swap_free': swap_free,
        },
        'nr_services': len(scol.list_services())
    }
    return jsonify(output)
