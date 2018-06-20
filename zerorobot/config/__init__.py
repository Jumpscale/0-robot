"""
module where we store global configuration used thoughout the robot
code base
"""
import gevent.event

from .data_repo import DataRepo
from .config_repo import ConfigRepo

SERVICE_LOADED = gevent.event.Event()

data_repo = None
config_repo = None

mode = None

webhooks = None
