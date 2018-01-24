"""
this module is the only place where the templates will be kept in memory.
other services and class need to use this module method to load/access the templates
"""

import importlib.util
import os
import re
import sys

from js9 import j
from zerorobot import service_collection as scol
from zerorobot.template_uid import TemplateUID

logger = j.logger.get('zerorobot')

_url_pattern_ssh = re.compile('^(git@)(.*?):(.*?)/(.*?)/?$')
_url_pattern_ssh2 = re.compile('^(git@)(.*?)/(.*?)/(.*?)/?$')
_url_pattern_http = re.compile('^(https?://)(.*?)/(.*?)/(.*?)/?$')


_templates = {}


def add_repo(url, branch='master', directory='templates'):
    """
    url: url of a git repository e.g: http://github.com/jumpscale/zeroroot
    branch: the branch of the repository to checkout
    directory: the path to the directory where the templates are located in the repository
    """
    new_templates = []
    dir_path = _git_path(url)
    if not os.path.exists(dir_path):
        dir_path = j.clients.git.pullGitRepo(url)
    for path in j.sal.fs.listDirsInDir(j.sal.fs.joinPaths(dir_path, directory)):
        if j.sal.fs.getBaseName(path) == '__pycache__':
            continue
        new_templates.append(_load_template(url, path))
    return new_templates


def get(uid):
    """
    @uid: unique identifier for a template.
    Can be a string with valid format as : 'github.com/account/repository/name/version'
    or
    a zerorobot.template_collection.TemplateUID object
    """
    if isinstance(uid, str):
        uid = TemplateUID.parse(uid)
    if uid not in _templates:
        raise KeyError("template with name %s not found" % str(uid))
    return _templates[uid]


def list_templates():
    return list(_templates.values())


def _parse_git_url(url):
    """
    return (protocol, repository_host, repository_account, repository_name)
    """
    sshmatch = _url_pattern_ssh.match(url)
    sshmatch2 = _url_pattern_ssh2.match(url)
    httpmatch = _url_pattern_http.match(url)
    if sshmatch:
        match = sshmatch
    elif sshmatch2:
        match = sshmatch2
    elif httpmatch:
        match = httpmatch
    else:
        raise RuntimeError(
            "Url is invalid. Must be in the form of 'http(s)://hostname/account/repo' or 'git@hostname:account/repo'\nnow:\n%s" % url)

    protocol, repository_host, repository_account, repository_name = match.groups()
    repository_name = repository_name.split('.git')[0]
    return (protocol, repository_host, repository_account, repository_name)


def _git_path(url):
    """
    return the location on the filesystem where a git repo would be cloned
    """
    _, host, account, name = _parse_git_url(url)
    host = host.split('.')[0]
    dest = '%(codedir)s/%(type)s/%(account)s/%(repo_name)s' % {
        'codedir': j.dirs.CODEDIR,
        'type': host.lower(),
        'account': account.lower(),
        'repo_name': name,
    }
    return dest.split('.git')[0]


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

    if class_name not in module.__dict__:
        raise TemplateNameError("template %s should contain a class called %s" % (template_name, class_name))

    class_ = eval('module.%s' % class_name)

    _, host, account, repo = _parse_git_url(url)

    class_.template_uid = TemplateUID.parse("%s/%s/%s/%s/%s" % (host, account, repo, template_name, class_.version))

    class_.template_dir = template_dir
    _templates[class_.template_uid] = class_
    logger.debug("add template %s to collection" % class_.template_uid)
    return _templates[class_.template_uid]


def instantiate_service(template, name=None, data=None):
    if isinstance(template, str):
        template = get(template)

    service = template(data=data, name=name)

    scol.add(service)
    return service


class TemplateNameError(Exception):
    pass
