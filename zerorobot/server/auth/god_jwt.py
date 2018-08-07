from functools import wraps
import os

from zerorobot import config
from jose import jwt
from jumpscale import j

logger = j.logger.get('zrobot')
_token_prefix = "Bearer "


def create():
    """create a JWT with the claims
    """
    claims = {'authentication': 'god_token'}
    key = _get_key()
    return jwt.encode(claims, key, algorithm='HS256')  # using HS256 algorithm


def decode(token):
    key = _get_key()
    return jwt.decode(token, key, algorithms='HS256')


def verify(token):
    if not token or not config.god:
        return False

    expected = {'authentication': 'god_token'}
    try:
        claims = decode(token)
        if claims == expected:
            return True
    except Exception as err:
        logger.error('error decoding god token: %s', str(err))

    return False


def check_god_token(request):
    # if god mode is not enabled on the service, no point going further
    if not config.god:
        return False

    if 'ZrobotSecret' not in request.headers:
        return False

    ss = request.headers['ZrobotSecret'].split(' ', 1)
    if len(ss) != 2:
        return False

    auth_type = ss[0]
    tokens = ss[1]
    if auth_type != 'Bearer' or not tokens:
        return []

    for token in tokens.split(' '):
        if verify(token):
            return True

    return False


def _get_key():
    """return the signing key to create JWT
    the key is the one used by the config manager of JumpScale

    Raises:
        SigningKeyNotFoundError -- [raised if signin key is not found]

    Returns:
        str -- the signing key
    """
    if j.tools.configmanager.keyname is None or j.tools.configmanager.keyname == '':
        raise SigningKeyNotFoundError('no key configured')

    key_path = os.path.expanduser(os.path.join('~/.ssh', j.tools.configmanager.keyname))
    if not os.path.exists(key_path):
        raise SigningKeyNotFoundError('key not found')

    return j.sal.fs.fileGetContents(key_path)


class SigningKeyNotFoundError(Exception):
    pass
