"""
this module is the only place where the templates will be kept in memory.
other services and class need to use this module method to load/access the templates
"""

import importlib.util
import os
import sys

from gevent.pool import Pool

from js9 import j
from zerorobot import service_collection as scol
from zerorobot import git
from zerorobot.service_collection import ServiceConflictError
from zerorobot.template_uid import TemplateUID

logger = j.logger.get('zerorobot')

_templates = {}


def add_repo(url, branch=None, directory='templates'):
    """
    url: url of a git repository e.g: http://github.com/jumpscale/zeroroot
    branch: the branch of the repository to checkout
    directory: the path to the directory where the templates are located in the repository
    """
    new_templates = []
    dir_path = git.url.git_path(url)

    if not os.path.exists(dir_path):
        if branch is None:
            branch = 'master'
        dir_path = j.clients.git.pullGitRepo(url, branch=branch)
    else:
        # if we didn't specify the branch and we already have the repo locally,
        # don't switch branch, this is usefull when developping on different branches
        repo = j.clients.git.get(dir_path)
        if branch is not None and repo.branchName != branch:
            repo.switchBranch(branch)

    for path in j.sal.fs.listDirsInDir(j.sal.fs.joinPaths(dir_path, directory)):
        if j.sal.fs.getBaseName(path) == '__pycache__':
            continue
        new_templates.append(_load_template(url, path))
    return new_templates


def get(uid):
    """Get a template class

    Arguments:
        uid {string|TemplateUID} -- unique identifier for a template.
                                    Can be a string with valid format as : 'github.com/account/repository/name/version'
                                    or a zerorobot.template_collection.TemplateUID object
                                    or a string which is the name of the template you want
                                    if 2 templates are loaded that have the same name TemplateConflictError is raised

    Raises:
        TemplateNotFoundError -- template with specified uid is not found
        TemplateConflictError -- raise if 2 templates have the same name is raised

    Returns:
        [TemplateBase] -- return the template class
    """
    if isinstance(uid, str):
        try:
            uid = TemplateUID.parse(uid)
        except ValueError:
            # uid is not a full template uid, try with only its name
            templates = find(name=uid)
            size = len(templates)
            if size > 1:
                raise TemplateConflictError("tried to get template with name %s, but more then one template have this name (%s)",
                                            uid, ','.join(templates))
            elif size <= 0:
                raise TemplateNotFoundError("template with name %s not found" % str(uid))
            else:
                return templates[0]

    if uid not in _templates:
        raise TemplateNotFoundError("template with name %s not found" % str(uid))
    return _templates[uid]


def find(host=None, account=None, repo=None, name=None, version=None):
    """
    search for a template based on the part of the template UID
    """
    match = []
    for uid, template in _templates.items():
        if host and uid.host != host:
            continue
        if account and uid.account != account:
            continue
        if repo and uid.repo != repo:
            continue
        if name and uid.name != name:
            continue
        if version and uid.version != version:
            continue
        match.append(template)
    return match


def list_templates():
    return list(_templates.values())


def _load_template(url, template_dir):
    """
    load a template in memory from a file
    The file must contain a class that inherits from template.TemplateBase
    and the name of the class must match the name of the file.
    the name of the class is camelcased from the name of the file.
    ex:
        node.py -> Node
        vm_manager.py -> VmManager
        a_long_name.py -> ALongName
    """
    template_name = os.path.basename(template_dir).split('.')[0]
    class_name = template_name.replace('_', ' ').title().replace(' ', '')
    class_path = os.path.join(template_dir, template_name + '.py')

    spec = importlib.util.spec_from_file_location(template_name, class_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module.__name__] = module

    if class_name not in module.__dict__:
        raise TemplateNameError("template %s should contain a class called %s" % (template_name, class_name))

    class_ = eval('module.%s' % class_name)

    _, host, account, repo = git.url.parse(url)

    class_.template_uid = TemplateUID.parse("%s/%s/%s/%s/%s" % (host, account, repo, template_name, class_.version))

    class_.template_dir = template_dir
    _templates[class_.template_uid] = class_
    logger.debug("add template %s to collection" % class_.template_uid)
    return _templates[class_.template_uid]


def instantiate_service(template, name=None, data=None):
    if isinstance(template, str):
        template = get(template)

    existing = scol.find(template_uid=str(template.template_uid), name=name)
    if name and len(existing) > 0:
        raise ServiceConflictError(
            message="a service with name=%s already exist" % name,
            service=existing[0])

    service = template(data=data, name=name)
    service.validate()
    service.save()

    scol.add(service)
    return service


def checkout_repo(url, revision='master'):
    logger.info("checkout %s for repo %s", revision, url)
    dir_path = git.url.git_path(url)

    if not os.path.exists(dir_path):
        raise TemplateNotFoundError()

    repo = git.repo.Repo(dir_path)
    repo.fetch()

    repo.repo.checkout(revision)
    t, _ = repo.branch_or_tag()
    if t == 'branch':
        repo.pull()

    # load the new templates
    logger.info("reload templates")
    updated_templates = add_repo(url)

    # pool of greenlet used to upgrade service concurrently
    pool = Pool(25)
    for template in updated_templates:
        for service in scol.find(template_host=template.template_uid.host,
                                 template_account=template.template_uid.account,
                                 template_repo=template.template_uid.repo,
                                 template_name=template.template_uid.name):
            pool.spawn(scol.upgrade, service, template, True)
    pool.join(raise_error=True)


class TemplateNameError(Exception):
    pass


class TemplateNotFoundError(KeyError):
    """
    This exception is raised when trying to create a service
    from a template that doesn't exists
    """
    pass


class TemplateConflictError(Exception):
    """
    This exception is raised when trying to get a template with its name
    and 2 templates have te same name, so we can't decide which one to retrn
    """
    pass
