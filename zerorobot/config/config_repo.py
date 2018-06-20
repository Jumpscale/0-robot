"""
data_repo module hold the logic of the configuration of the jumpscale configuration repository
"""

import os

from js9 import j
from zerorobot.git import url as giturl

from .auto_pusher import AutoPusher

STANDARD_CONFIG_DIR = os.path.join(j.dirs.CODEDIR, 'local/stdorg/config')


class ConfigRepo:

    def __init__(self, url=None, key=None):
        self.url = url
        self.path = None
        self.auto_pusher = None
        self._init(url, key)

    @property
    def last_pushed(self):
        if not self.auto_pusher:
            return None
        return self.auto_pusher.last_pushed

    def start_auto_push(self, interval=60, logger=None):
        self.auto_pusher = AutoPusher(interval, self.path, logger)
        self.auto_pusher.run()

    def _init(self, url, key):
        # initialize a jumpscale configuration repository
        if not url:
            tmp = _is_path_configure()
            path = tmp if tmp else STANDARD_CONFIG_DIR
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

        if not os.path.exists(path):
            os.makedirs(path)

        if key is None:
            # try to detect if jumpscale has a key configured
            tmp = _is_key_configured()
            if tmp:
                key = tmp
            else:
                # no key configured, generate a new one
                key = os.path.expanduser(os.path.join('~/.ssh', j.data.idgenerator.generateXCharID(8)))
                j.sal.ubuntu.sshkeys_generate(path=key)
        else:
            # key is specified, ensure it actually exists
            if not os.path.exists(key):
                raise ValueError("ssh key specified (%s) doesn't exists" % key)

        j.tools.configmanager.init(silent=True, configpath=path, keypath=key)
        self.path = path
        self.key = key


def _is_path_configure():
    #  try to detect if a config report us configure in jumpscale
    path = None
    myconfig = j.core.state.config_js.get('myconfig')
    if myconfig:
        p = myconfig.get('path')
        if p and os.path.exists(p):
            path = p
    return path


def _is_key_configured():
    # try to detect if jumpscale has a key configured
    if j.tools.configmanager.keyname is None or j.tools.configmanager.keyname == '':
        return None

    key_path = os.path.expanduser(os.path.join('~/.ssh', j.tools.configmanager.keyname))
    if os.path.exists(key_path):
        return key_path

    return None
