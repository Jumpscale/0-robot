import logging
import os
import shlex
import signal
import time

import gevent
from gevent import GreenletExit
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer

from js9 import j
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot import config, webhooks
from zerorobot.git import url as giturl
from zerorobot.prometheus.flask import monitor
from zerorobot.server import auth
from zerorobot.server.app import app

from . import loader

# create logger
logger = j.logger.get('zerorobot')


class Robot:
    """
    A robot is the main context where the templates and service lives.
    It is responsible to:
        - run the REST API server
        - download the template from a git repository
        - load the templates in memory and make them available
    """

    def __init__(self):
        self._started = False
        self._block = True
        self.data_repo_url = None
        self._http = None  # server handler
        self.addr = None
        self._sig_handler = []

    @property
    def address(self):
        if self._http:
            return self._http.address
        return None

    def set_data_repo(self, url):
        """
        Set the data repository used to serialize services state.

        @param path: can be a git URL or a absolute path or None
            if git url: clone the repository locally, and use it as configuration repo
            if absolute path: make sure the directory exist and use it as configuration repo
            if None: automatically create a configuration repository in `{j.dirs.DATADIR}/zrobot`

        It can be the same of one of the template repository used.
        """
        config.data_repo = config.DataRepo(url)
        self.data_repo_url = url

    def add_template_repo(self, url, directory='templates'):
        url, branch = giturl.parse_template_repo_url(url)
        tcol.add_repo(url=url, branch=branch, directory=directory)

    def set_config_repo(self, url=None, key=None):
        """
        make sure the jumpscale configuration repository is initialized
        @param path: can be a git URL or a absolute path or None
            if git url: clone the repository locally, and use it as configuration repo
            if absolute path: make sure the directory exist and use it as configuration repo
            if None: automatically create a configuration repository in `{j.dirs.CODEDIR}/local/stdorg/config`

        @param key: path to the sshkey to use with the configuration repo
        if key is None, a key is automatically generated
        """
        config.config_repo = config.ConfigRepo(url=url, key=key)

    def start(self,
              listen=":6600",
              log_level=logging.DEBUG,
              block=True,
              auto_push=False,
              auto_push_interval=60,
              admin_organization=None,
              user_organization=None,
              mode=None,
              god=False,
              **kwargs):
        """
        start the rest web server
        load the services from the local git repository
        """
        config.mode = mode
        config.god = god  # when true, this allow to get data and logs from services using the REST API

        if config.data_repo is None or config.data_repo.path is None:
            raise RuntimeError("Not data repository set. Robot doesn't know where to save data.")

        if not j.tools.configmanager.path:
            raise RuntimeError("config manager is not configured, can't continue")

        # instantiate webhooks manager and load the configured webhooks
        config.webhooks = webhooks.Storage(config.data_repo.path)
        config.webhooks.load()

        logger.info("data directory: %s" % config.data_repo.path)
        logger.info("config directory: %s" % j.tools.configmanager.path)
        logger.info("sshkey used: %s" % os.path.expanduser(os.path.join('~/.ssh', j.tools.configmanager.keyname)))

        # configure prometheus monitoring
        if not kwargs.get('testing', False):
            monitor(app)

         # configure authentication middleware
        _configure_authentication(admin_organization, user_organization)

        self._block = block

        self._sig_handler.append(gevent.signal(signal.SIGINT, self.stop))

        # configure logger
        app._logger = logger

        # auto-push data repo
        if auto_push:
            logger.info("auto push of data repo enabled")
            config.data_repo.start_auto_push(interval=auto_push_interval, logger=logger)
            config.config_repo.start_auto_push(interval=auto_push_interval, logger=logger)

        # load services from data repo
        loader.load_services(config.data_repo.path)
        # notify services that they can start processing their task list
        config.SERVICE_LOADED.set()

        if mode == 'node':
            _create_node_service()

        # only keep executed tasks for 2 hours
        gevent.spawn(_trim_tasks, 7200)

        # using a pool allow to kill the request when stopping the server
        pool = Pool(None)
        hostport = _split_hostport(listen)
        self._http = WSGIServer(hostport, app, spawn=pool, log=logger, error_log=logger)
        self._http.start()
        logger.info("robot running at %s:%s" % hostport)

        if block:
            self._http.serve_forever()
            # this is executed when self.stop is called.
            # here no more requests are comming in, we can safely save all services
            self._save_services()
        else:
            self._http.start()

    def stop(self):
        """
        stop receiving requests
        gracefully stop all the services
        serialize all services state to disk
        """
        # prevent the signal handler to be called again if
        # more signal are received
        for h in self._sig_handler:
            h.cancel()

        logger.info('stopping robot')
        self._http.stop()
        self._http = None

        # if we don't block, we can gracefully shutdown here
        # cause we're not in a sig handler
        if self._block is False:
            # here no more requests are comming in, we can safely save all services
            self._save_services()

    def _save_services(self):
        """
        serialize all the services on disk
        """
        for service in scol.list_services():
            # stop all the greenlets attached to the services
            service.gl_mgr.stop_all()
            service.save()


def _create_node_service():
    service_found = scol.find(template_host='github.com', template_account='zero-os', template_name='node')
    if not service_found:
        template_found = tcol.find(host='github.com', account='zero-os', name='node')
        if not template_found:
            tcol.add_repo("https://github.com/zero-os/0-templates")

        template_found = tcol.find(host='github.com', account='zero-os', name='node')
        if not template_found:
            raise RuntimeError("cannot create node service and --mode node is set")

        logger.info("create node service because --mode node is net")
        node = tcol.instantiate_service(template_found[0], 'local', {})
    else:
        node = service_found[0]

    try:
        node.state.check('actions', 'install', 'ok')
    except:
        node.schedule_action('install')
    node.schedule_action('_register')


def _trim_tasks(period=7200):  # default 2 hours ago
    """
    this greenlet delete the task of all services that are older
    then 'period'
    This is to limit the amount of storage used to keep track of the tasks
    """
    while True:
        try:
            time.sleep(20*60)  # runs every 20 minutes
            ago = int(time.time()) - period

            for service in scol.list_services():
                if not hasattr(service.task_list._done, 'delete_until'):
                    continue
                # delete all task that have been created before ago
                service.task_list._done.delete_until(ago)
        except gevent.GreenletExit:
            # exit properly
            return
        except:
            logger.exception("error deleting old tasks")
            continue


def _split_hostport(hostport):
    """
    convert a listen addres of the form
    host:port into a tuple (host, port)
    host is a string, port is an int
    """
    i = hostport.index(':')
    host = hostport[:i]
    port = hostport[i + 1:]
    return host, int(port)


def _configure_authentication(admin_organization, user_organization):
    if admin_organization:
        auth.auth.admin_organization = admin_organization
        logger.info("admin JWT authentication enabled for organization: %s" % auth.auth.admin_organization)
    if user_organization:
        auth.auth.user_organization = user_organization
        logger.info("user JWT authentication enabled for organization: %s" % auth.auth.user_organization)
