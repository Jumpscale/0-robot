import os

import gevent

from js9 import j
from zerorobot import service_collection as scol
from zerorobot import template_collection as tcol
from zerorobot.robot import config
from zerorobot.template_uid import TemplateUID

logger = j.logger.get('zerorobot')


def load_services(data_dir):
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    for srv_dir in j.sal.fs.listDirsInDir(data_dir, recursive=True):
        info_path = os.path.join(srv_dir, 'service.yaml')
        if not os.path.exists(info_path):
            continue
        service_info = j.data.serializer.yaml.load(info_path)

        tmpl_uid = TemplateUID.parse(service_info['template'])
        try:
            tmplClass = tcol.get(str(tmpl_uid))
        except tcol.TemplateNotFoundError:
            # template of the service not found, could be we have the template but not the same version
            # try to get the template without specifiying version
            tmplClasses = tcol.find(host=tmpl_uid.host, account=tmpl_uid.account, repo=tmpl_uid.repo, name=tmpl_uid.name)
            size = len(tmplClasses)
            if size > 1:
                raise RuntimeError("more then one template version found, this should never happens")
            elif size < 1:
                # if the template is not found, try to add the repo using the info of the service template uid
                url = "http://%s/%s/%s" % (tmpl_uid.host, tmpl_uid.account, tmpl_uid.repo)
                tcol.add_repo(url)
                tmplClass = tcol.get(service_info['template'])
            else:
                # template of another version found, use newer version to load the service
                tmplClass = tmplClasses[0]

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
