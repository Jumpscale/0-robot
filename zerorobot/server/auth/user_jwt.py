from functools import wraps
import os

from jose import jwt
from js9 import j

logger = j.logger.get('zrobot')
_token_prefix = "Bearer "


def create(claims):
    """create a JWT with the claims pass as argument

    Arguments:
        claims {dict} -- dict of claims to include in the JWT
    """
    key = _get_key()
    return jwt.encode(claims, key, algorithm='HS256')


def decode(token):
    key = _get_key()
    return jwt.decode(token, key, algorithms='HS256')


def verify(service_guid, token):
    if not token:
        return False

    expected = {'service_guid': service_guid}
    try:
        claims = decode(token)
        if claims == expected:
            return True
    except Exception as err:
        logger.error('error decoding user secret: %s', str(err))

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
