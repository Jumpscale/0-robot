"""
data_repo module hold the logic of the configuration of the jumpscale configuration repository
"""

from zerorobot import giturl
from js9 import j
import os


def ensure(path=None):
    """
    ensure the 0-robot data repository exists
    """
    if not path:
        # no path specify, we create one
        path = j.sal.fs.joinPaths(j.core.dirs.DATADIR, 'zrobot')
    else:
        try:
            # try to see of path is a git URL
            url = path
            path = giturl.git_path(url)
            # if the repo is not clone yet, clone it now
            if not os.path.exists(path):
                path = j.clients.git.pullGitRepo(url)
        except ValueError:
            # path is not an URL, we expect an absolute path
            if not os.path.isabs(path):
                raise ValueError("path value is not valid. Need to be a valid git url or an absolute path on the local filesystem")

    if not os.path.exists(path):
        os.makedirs(path)

    return path
