"""
this module contain class that are used to store the data repository configration of the robot
"""

import os
from urllib.parse import urlparse

from jumpscale import j
from zerorobot.git import url as giturl

from .auto_pusher import AutoPusher


class DataRepo:

    def __init__(self, url):
        self.url = None
        self.path = None
        self.auto_pusher = None
        self.username = None
        self.password = None
        self.hostname = None
        self.port = None
        self.type = None

        if not url:
            # no path/url specify, we create one
            path = j.sal.fs.joinPaths(j.core.dirs.DATADIR, 'zrobot')
        else:
            # url points to a zdb
            try:
                self.username, self.password, self.hostname, self.port = _parse_zdb(url)
                self.type = 'zdb'
                return
            except ValueError:
                # not a zdb url, try git url
                pass

            try:
                # try to see of path is a git URL
                path = giturl.git_path(url)
                self.url = url
                # if the repo is not clone yet, clone it now
                if not os.path.exists(path):
                    path = j.clients.git.pullGitRepo(url)
            except ValueError:
                # not a zdb url, try absolute path
                path = url

            # path is not an URL, we expect an absolute path
            if not os.path.isabs(path):
                raise ValueError("path value is not valid. Need to be a valid git url or an absolute path on the local filesystem")

        path = os.path.join(path, 'zrobot_data')

        if not os.path.exists(path):
            os.makedirs(path)

        self.path = path
        self.type = 'fs'

    @property
    def last_pushed(self):
        if not self.auto_pusher:
            return None
        return self.auto_pusher.last_pushed

    def start_auto_push(self, interval=60, logger=None):
        self.auto_pusher = AutoPusher(interval, self.path, logger)
        self.auto_pusher.run()


def _parse_zdb(line):
    """
    parse a zdb url

    zdb://username:password@hostname:port'

    return (username, password, hostname, port)
    """

    u = urlparse(line)
    if u.scheme != 'zdb':
        raise ValueError('scheme should be bcdb, not %s', u.scheme)

    return (u.username, u.password, u.hostname, u.port)
