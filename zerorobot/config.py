"""
module where we store global configuration used thoughout the robot
code base
"""
import gevent.event

# path to the data director where to save the services
DATA_DIR = None

SERVICE_LOADED = gevent.event.Event()
