from prometheus_client import Gauge, Histogram
from zerorobot import service_collection as scol
import psutil
import os

# tasks
nr_task_waiting = Gauge("robot_tasks_waiting_total", "Number of task waiting per service", ['service_guid'])
task_latency = Histogram('robot_tasks_latency_ms', 'Task latency',
                         ['action_name', 'template_uid'])


process = psutil.Process(os.getpid())


def memory_usage_resource():
    return process.memory_info().rss


def monitor_robot_metrics():
    # services
    nr_services = Gauge("robot_services_total", "Number of services running")
    nr_services.set_function(lambda: len(scol.list_services()))
    # memory
    robot_memory = Gauge('robot_total_memory_bytes', "Memory used by 0-robot")
    robot_memory.set_function(lambda: memory_usage_resource())
