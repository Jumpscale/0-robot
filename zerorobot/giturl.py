"""
this module contains utility to parse git URL
"""

import re
import urllib

from js9 import j

_url_pattern_ssh = re.compile('^(git)@(.*?):(.*?)/(.*?)/?$')
_url_pattern_ssh2 = re.compile('^(git)@(.*?)/(.*?)/(.*?)/?$')
_url_pattern_ssh3 = re.compile('^ssh://(git)@(.*?)/(.*?)/(.*?)/?$')
_url_pattern_http = re.compile('^(https?)://(.*?)/(.*?)/(.*?)/?$')
_url_patterns = (_url_pattern_ssh, _url_pattern_ssh2, _url_pattern_ssh3, _url_pattern_http)


def parse(url):
    """
    return (protocol, repository_host, repository_account, repository_name)
    """
    match = None
    for pattern in _url_patterns:
        m = pattern.match(url)
        if m:
            match = m
            break

    if not match:
        raise RuntimeError(
            "Url is invalid. Must be in the form of 'http(s)://hostname/account/repo', 'git@hostname:account/repo' or 'ssh://git@hostname/account/repo' \nnow:\n%s" % url)

    protocol, repository_host, repository_account, repository_name = match.groups()
    repository_name = repository_name.split('.git')[0]
    repository_host = urllib.parse.splitport(repository_host)[0]
    return (protocol, repository_host, repository_account, repository_name)


def git_path(url):
    """
    return the location on the filesystem where a git repo would be cloned
    """
    _, host, account, name = parse(url)
    host = host.split('.')[0]
    dest = '%(codedir)s/%(type)s/%(account)s/%(repo_name)s' % {
        'codedir': j.dirs.CODEDIR,
        'type': host.lower(),
        'account': account.lower(),
        'repo_name': name,
    }
    return dest.split('.git')[0]


def parse_template_repo_url(url):
    branch = None

    protocol, _, _, _ = parse(url)

    if protocol in ('ssh', 'git'):
        ss = url.split('#')
        if len(ss) > 1:
            return ss[0], ss[1]
        return url, None

    u = urllib.parse.urlparse(url)
    if u.fragment:
        branch = u.fragment

    return u.scheme+'://'+u.netloc+u.path, branch
