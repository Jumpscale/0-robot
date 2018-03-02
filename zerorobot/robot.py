"""
robot modules define the Robot class

It is the class responsible to start and managed the robot as well as the REST API.
"""

import logging
import os
import signal

import gevent
from gevent import GreenletExit
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer

from js9 import j
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot.prometheus.flask import monitor
from zerorobot.server.app import app
from zerorobot import config

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
        Set the url of the git repository to be used to serialize services state.
        It can be the same of one of the template repository used.
        """
        location = tcol._git_path(url)
        if not os.path.exists(location):
            location = j.clients.git.pullGitRepo(url)

        self.data_repo_url = url
        config.DATA_DIR = j.sal.fs.joinPaths(location, 'zrobot_data')

    def add_template_repo(self, url, branch='master', directory='templates'):
        tcol.add_repo(url=url, branch=branch, directory=directory)

    def set_config_repo(self, url):
        """
        Set the url of the configuration repository used by JumpScale to store client configuration
        It can be the same URL as the data repository.
        """
        location = tcol._git_path(url)
        if not os.path.exists(location):
            location = j.clients.git.pullGitRepo(url)
            j.sal.fs.createEmptyFile(os.path.join(location, '.jsconfig'))
        j.tools.configmanager._path = location

    def start(self, listen=":6600", log_level=logging.DEBUG, block=True, **kwargs):
        """
        start the rest web server
        load the services from the local git repository
        """
        if config.DATA_DIR is None:
            raise RuntimeError("Not data repository set. Robot doesn't know where to save data.")

        logger.info("data directory: %s" % config.DATA_DIR)

        # FIXME: I need way to know there is a properly inited config repo
        # will raise if not config repo is found
        # if not j.tools.configmanager.path:
        #     raise RuntimeError("config manager is not configured, can't continue")

        # configure prometheus monitoring
        if not kwargs.get('testing', False):
            monitor(app)

        self._block = block

        self._sig_handler.append(gevent.signal(signal.SIGINT, self.stop))

        # configure logger
        app._logger = logger

        # using a pool allow to kill the request when stopping the server
        pool = Pool(None)
        hostport = _split_hostport(listen)
        self._http = WSGIServer(hostport, app, spawn=pool, log=logger, error_log=logger)
        self._http.start()

        logger.info("robot running at %s:%s" % hostport)

        # load services from data repo
        self._load_services()

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

    def _load_services(self):
        if not os.path.exists(config.DATA_DIR):
            os.makedirs(config.DATA_DIR)

        for srv_dir in j.sal.fs.listDirsInDir(config.DATA_DIR, recursive=True):
            info_path = os.path.join(srv_dir, 'service.yaml')
            if not os.path.exists(info_path):
                continue
            service_info = j.data.serializer.yaml.load(info_path)
            tmplClass = tcol.get(service_info['template'])
            srv = scol.load(tmplClass, srv_dir)

        loading_failed = []
        for service in scol.list_services():
            try:
                service.validate()
            except Exception as err:
                logger.error("fail to load %s: %s" % (service.guid, str(err)))
                # the service is not going to process its task list until it can
                # execute validate() without problem
                service.gl_mgr.stop('executor')
                loading_failed.append(service)

        if len(loading_failed) > 0:
            gevent.spawn(_try_load_service, loading_failed)

    def _save_services(self):
        """
        serialize all the services on disk
        """
        for service in scol.list_services():
            # stop all the greenlets attached to the services
            service.gl_mgr.stop_all()
            service.save()


def _try_load_service(services):
    """
    this method tries to execute `validate` method on the services that failed to load
    when the robot started.
    Once all failed services are back to normal, this function will exit
    """
    size = len(services)
    while size > 0:
        for service in services[:]:
            try:
                logger.debug("try to load %s again" % service.guid)
                service.validate()
                logger.debug("loading succeeded for %s" % service.guid)
                # validate passed, service is healthy again
                service.gl_mgr.add('executor', gevent.Greenlet(service._run))
                services.remove(service)
            except:
                logger.debug("loading failed again for %s" % service.guid)
        gevent.sleep(10)  # fixme: why 10 ? why not?
        size = len(services)


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
