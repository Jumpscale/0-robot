from functools import wraps
import os

from jose import jwt
from js9 import j

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
    except:
        pass  # return False
    return False


def _get_key():
    """return the signing key to create JWT
    the key is the one used by the config manager of JumpScale

    Raises:
        SigningKeyNotFoundError -- [raised if signin key is not found]

    Returns:
        str -- the signing key
    """
    try:
        key_name = j.core.state.config_js['myconfig']['sshkeyname']
    except KeyError:
        raise SigningKeyNotFoundError()

    key_path = os.path.expanduser(os.path.join('~/.ssh', key_name))
    if not os.path.exists(key_path):
        raise SigningKeyNotFoundError()
    return j.sal.fs.fileGetContents(key_path)


class SigningKeyNotFoundError(Exception):
    pass
