from functools import wraps

from flask import jsonify, request
from flask_httpauth import HTTPTokenAuth, MultiAuth
from jose import jwt
from js9 import j
from zerorobot import service_collection as scol

from . import user_jwt

_oauth2_server_pub_key = """-----BEGIN PUBLIC KEY-----
MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAES5X8XrfKdx9gYayFITc89wad4usrk0n2
7MjiGYvqalizeSWTHEpnd7oea9IQ8T5oJjMVH5cc0H5tFSKilFFeh//wngxIyny6
6+Vq5t5B0V0Ehy01+2ceEon2Y0XDkIKv
-----END PUBLIC KEY-----"""
jwt_organization = None  # to be set at startup by robot class

admin = HTTPTokenAuth('Bearer')
user = HTTPTokenAuth('ZrobotAuth')
multi = MultiAuth(user, admin)


@admin.verify_token
def _verify_admin_token(token):
    if jwt_organization is None:
        return True

    allowed_scopes = ['user:memberof:%s' % jwt_organization]
    if allowed_scopes is None or len(allowed_scopes) == 0:
        return True

    try:
        scope = jwt.decode(token, _oauth2_server_pub_key, audience=None)["scope"]
    except:
        return False

    for allowed in allowed_scopes:
        for s in scope:
            if s == allowed:
                return True

    return False


@user.verify_token
def _verify_user_token(token):
    service_guid = request.view_args.get('service_guid')
    if not service_guid:
        return False

    return user_jwt.verify(service_guid, token)
