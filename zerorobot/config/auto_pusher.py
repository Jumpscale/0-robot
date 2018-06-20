import gevent
import datetime
from js9 import j

from zerorobot import service_collection as scol


class AutoPusher:

    def __init__(self, interval=60, repo_dir=None, logger=None):
        self.interval = interval
        self.repo_dir = repo_dir
        self.logger = logger
        self.last_pushed = None

        # checks if setup is properly configured for auto pushing the repo
        git = j.clients.git.get(basedir=self.repo_dir)
        remote = git.getConfig("remote.origin.url")
        if not remote:
            raise RuntimeError("data git repository doesn't have a remote set, don't know where to push")
        # check if remote is ssh
        if not _is_ssh_remote(remote):
            raise RuntimeError("The data repository is not an ssh endpoint which is required for auto pushing.")

        _load_ssh_key()

    def run(self):
        """
        runs auto push of provided repo directory in a greenlet
        provided interval is in minutes
        """
        gevent.spawn(self._auto_push)

    def _auto_push(self):
        """
        run a coroutine that pushes the repository at provided interval
        provided interval is in minutes
        meant to be run as gevent greenlet/coroutine
        """
        while True:
            self.logger.debug("waiting interval")
            # gevent.sleep(seconds=self.interval*60)
            gevent.sleep(seconds=self.interval)
            if self.logger is not None:
                self.logger.debug("saving services and pushing data repo")
            _load_ssh_key()

            # save all services
            for service in scol.list_services():
                service.save()

            git = j.clients.git.get(basedir=self.repo_dir)
            git.commit(message='zrobot sync', addremove=True)
            git.push()

            self.last_pushed = datetime.datetime.now()


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
