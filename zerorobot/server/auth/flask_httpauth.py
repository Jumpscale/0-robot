from functools import wraps
from flask import request, make_response
from werkzeug.datastructures import Authorization


class HTTPAuth(object):

    def __init__(self, scheme=None, realm=None, header='Authorization'):
        self.scheme = scheme
        self.realm = realm or "Authentication Required"
        self.header = header
        self.get_password_callback = None
        self.auth_error_callback = None

        def default_get_password(username):
            return None

        def default_auth_error():
            return "Unauthorized Access"

        self.get_password(default_get_password)
        self.error_handler(default_auth_error)

    def get_password(self, f):
        self.get_password_callback = f
        return f

    def error_handler(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            res = f(*args, **kwargs)
            res = make_response(res)
            if res.status_code == 200:
                # if user didn't set status code, use 401
                res.status_code = 401
            if 'WWW-Authenticate' not in res.headers.keys():
                res.headers['WWW-Authenticate'] = self.authenticate_header()
            return res
        self.auth_error_callback = decorated
        return decorated

    def authenticate_header(self):
        return '{0} realm="{1}"'.format(self.scheme, self.realm)

    def login_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if auth is None and self.header in request.headers:
                # Flask/Werkzeug do not recognize any authentication types
                # other than Basic or Digest, so here we parse the header by
                # hand
                try:
                    auth_type, token = request.headers[self.header].split(None, 1)
                    auth = Authorization(auth_type, {'token': token})
                except ValueError:
                    # The Authorization header is either empty or has no token
                    pass

            # if the auth type does not match, we act as if there is no auth
            # this is better than failing directly, as it allows the callback
            # to handle special cases, like supporting multiple auth types
            if auth is not None and auth.type.lower() != self.scheme.lower():
                auth = None

            # Flask normally handles OPTIONS requests on its own, but in the
            # case it is configured to forward those to the application, we
            # need to ignore authentication headers and let the request through
            # to avoid unwanted interactions with CORS.
            if request.method != 'OPTIONS':  # pragma: no cover
                if auth and auth.username:
                    password = self.get_password_callback(auth.username)
                else:
                    password = None
                if not self.authenticate(auth, password):
                    # Clear TCP receive buffer of any pending data
                    request.data
                    return self.auth_error_callback()

            return f(*args, **kwargs)
        return decorated

    def username(self):
        if not request.authorization:
            return ""
        return request.authorization.username


class HTTPTokenAuth(HTTPAuth):

    def __init__(self, scheme='Bearer', realm=None, header='Authorization'):
        super(HTTPTokenAuth, self).__init__(scheme, realm, header)

        self.verify_token_callback = None

    def verify_token(self, f):
        self.verify_token_callback = f
        return f

    def authenticate(self, auth, stored_password):
        if auth:
            token = auth['token']
        else:
            token = ""
        if self.verify_token_callback:
            return self.verify_token_callback(token)
        return False


class MultiAuth(object):

    def __init__(self, main_auth, *args):
        self.main_auth = main_auth
        self.additional_auth = args

    def login_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            selected_auth = None
            if 'Authorization' in request.headers:
                try:
                    scheme, creds = request.headers['Authorization'].split(
                        None, 1)
                except ValueError:
                    # malformed Authorization header
                    pass
                else:
                    for auth in self.additional_auth:
                        if auth.scheme == scheme:
                            selected_auth = auth
                            break
            if selected_auth is None:
                selected_auth = self.main_auth
            return selected_auth.login_required(f)(*args, **kwargs)
        return decorated
