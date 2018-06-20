"""
this module contain class that are used to store the data repository configration of the robot
"""

import os

from js9 import j
from zerorobot.git import url as giturl
from .auto_pusher import AutoPusher


class DataRepo:

    def __init__(self, url):
        self.url = url
        self.path = _ensure(url)
        self.auto_pusher = None

    @property
    def last_pushed(self):
        if not self.auto_pusher:
            return None
        return self.auto_pusher.last_pushed

    def start_auto_push(self, interval=60, logger=None):
        self.auto_pusher = AutoPusher(interval, self.path, logger)
        self.auto_pusher.run()


def _ensure(url):
    if not url:
        # no path/url specify, we create one
        path = j.sal.fs.joinPaths(j.core.dirs.DATADIR, 'zrobot')
    else:
        try:
            # try to see of path is a git URL
            path = giturl.git_path(url)
            # if the repo is not clone yet, clone it now
            if not os.path.exists(path):
                path = j.clients.git.pullGitRepo(url)
        except ValueError:
            # path is not an URL, we expect an absolute path
            path = url
            if not os.path.isabs(path):
                raise ValueError("path value is not valid. Need to be a valid git url or an absolute path on the local filesystem")

    path = os.path.join(path, 'zrobot_data')

    if not os.path.exists(path):
        os.makedirs(path)

    return path
