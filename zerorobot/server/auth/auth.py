from functools import wraps

from flask import jsonify, request
from jose import jwt
from js9 import j
from zerorobot import service_collection as scol
from zerorobot import config
from . import user_jwt, god_jwt
from .flask_httpauth import HTTPTokenAuth, MultiAuth

logger = j.logger.get('zrobot')

_oauth2_server_pub_key = """-----BEGIN PUBLIC KEY-----
MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAES5X8XrfKdx9gYayFITc89wad4usrk0n2
7MjiGYvqalizeSWTHEpnd7oea9IQ8T5oJjMVH5cc0H5tFSKilFFeh//wngxIyny6
6+Vq5t5B0V0Ehy01+2ceEon2Y0XDkIKv
-----END PUBLIC KEY-----"""

admin_organization = None  # to be set at startup by robot class
user_organization = None  # to be set at startup by robot class

admin = HTTPTokenAuth('Bearer', header='ZrobotAdmin')
user = HTTPTokenAuth('Bearer',  header='ZrobotUser')
service = HTTPTokenAuth('Bearer',  header='ZrobotSecret')

user_service = MultiAuth(user, service)
admin_user = MultiAuth(admin, user)
all = MultiAuth(admin, user, service)


def _verify_token(token, organization):
    if organization is None:
        return True

    allowed_scopes = ['user:memberof:%s' % organization]
    if allowed_scopes is None or len(allowed_scopes) == 0:
        return True

    try:
        scope = jwt.decode(token, _oauth2_server_pub_key, audience=None)["scope"]
    except Exception as err:
        logger.error('error decoding JWT: %s', str(err))
        return False

    for allowed in allowed_scopes:
        for s in scope:
            if s == allowed:
                return True

    return False


@admin.verify_token
def _verify_admin_token(token):
    return _verify_token(token, admin_organization)


@user.verify_token
def _verify_user_token(token):
    return _verify_token(token, user_organization)


@service.verify_token
def _verify_secret_token(tokens):
    service_guid = request.view_args.get('service_guid')
    if not service_guid:
        return False

    for token in tokens.split(' '):
        if god_jwt.verify(token) or user_jwt.verify(service_guid, token):
            return True

    try:
        if scol.is_service_public(service_guid):
            return True
    except scol.ServiceNotFoundError:
        return False

    return False
