"""
data_repo module hold the logic of the configuration of the jumpscale configuration repository
"""

from zerorobot import auto_pusher, config
from zerorobot.git import url as giturl
from js9 import j
import os

STANDARD_CONFIG_DIR = os.path.join(j.dirs.CODEDIR, 'local/stdorg/config')


def init(path=None, key=None):
    """
    initialize a jumpscale configuration repository
    """
    if not path:
        tmp = _is_path_configure()
        if tmp:
            path = tmp
        else:
            # no path specify, we create one
            path = STANDARD_CONFIG_DIR
    else:
        try:
            # try to see of path is a git URL
            url = path
            path = giturl.git_path(url)
            # if the repo is not clone yet, clone it now
            if not os.path.exists(path):
                location = j.clients.git.pullGitRepo(url)
        except ValueError:
            # path is not an URL, we expect an absolute path
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
            key = '/root/.ssh/%s' % j.data.idgenerator.generateXCharID(8)
            j.sal.ubuntu.sshkeys_generate(path=key)
    else:
        # key is specified, ensure it actually exists
        if not os.path.exists(key):
            raise ValueError("ssh key specified (%s) doesn't exists" % key)

    j.tools.configmanager.init(silent=True, configpath=path, keypath=key)
    return path


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
    key = None
    myconfig = j.core.state.config_js.get('myconfig')
    if myconfig:
        key_name = myconfig.get('sshkeyname')
        if key_name:
            key_path = os.path.join('%s/.ssh' % j.dirs.HOMEDIR, key_name)
            if os.path.exists(key_path):
                key = key_path
    return key
