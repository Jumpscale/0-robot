import gevent
from js9 import j

from zerorobot import service_collection as scol

def run(interval=60, repo_dir="", logger=None):
    """
    runs auto push of provided repo directory in a greenlet
    provided interval is in minutes
    """
    _init_auto_push(repo_dir=repo_dir)
    gevent.spawn(_auto_push_data_repo, interval, repo_dir, logger)

def _init_auto_push(repo_dir=""):
    """
    checks if setup is properly configured for auto pushing the repo
    """
    # check if remote is ssh
    git = j.clients.git.get(basedir=repo_dir)
    remote = git.getConfig("remote.origin.url")
    if not _is_ssh_remote(remote):
        raise RuntimeError("The data repository is not an ssh endpoint which is required for auto pushing.")
    
    _load_ssh_key()

def _auto_push_data_repo(interval=60, repo_dir="", logger=None):
    """
    run a coroutine that pushes the repository at provided interval
    provided interval is in minutes
    meant to be run as gevent greenlet/coroutine
    """
    while True:
        logger.debug("waiting interval")
        gevent.sleep(seconds=interval*60)
        if logger is not None:
            logger.debug("saving services and pushing data repo")
        _load_ssh_key()
        
        # save all services
        for service in scol.list_services():
            service.save()

        _push_data_repo(repo_dir=repo_dir)

def _push_data_repo(repo_dir=""):
    """
    commit and push (full) repository
    """
    git = j.clients.git.get(basedir=repo_dir)
    git.commit(message='zrobot sync', addremove=True)
    git.push()

def _load_ssh_key():
    """
    makes sure ssh key `j.tools.configmanager.keyname` is loaded
    """
    keyname = j.tools.configmanager.keyname
    key = j.clients.sshkey.get(keyname)
    key.load()

def _is_ssh_remote(url):
    if url.startswith("ssh://") or url.startswith('git@'):
        return True
    return False
