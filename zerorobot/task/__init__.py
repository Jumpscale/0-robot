# Task state constant
TASK_STATE_NEW = "new"
TASK_STATE_RUNNING = "running"
TASK_STATE_OK = "ok"
TASK_STATE_ERROR = "error"


# has the highest priority, usually used by the robot when it needs a service to execute something
PRIORITY_SYSTEM = 0
# priority used for recurring action, need to be higher then normal actions
PRIORITY_RECURRING = 5
# default value used when an action is schedule from normal user API
PRIORITY_NORMAL = 10

# public class of the package
from .task import Task
from .task_list import TaskList
from .storage.base import TaskNotFoundError
