import time

from jumpscale import j

from .client import Client

JSConfigClientBase = j.tools.configmanager.base_class_config


_template = """
url = "http://localhost:6600"
jwt_ = ""
secrets_ = []
god_token_ = ""
"""


class ZeroRobotClient(JSConfigClientBase):

    def __init__(self, instance="main", data={}, parent=None, template=None, ui=None, interactive=True):
        """
        @param instance: instance name
        @param data: configuration data. if specified will update the configuration with it
        @param parent: used by configmanager, you probably don't need to deal with it manually
        """
        data = data or {}
        super().__init__(instance=instance, data=data, parent=parent, template=_template, ui=ui, interactive=interactive)
        self._api = None
        self._jwt_expire_timestamp = None

    @property
    def api(self):
        """
        regroup all of the method to talk to the ZeroRobot API
        """
        jwt = self.config.data.get('jwt_')
        if jwt and not self._jwt_expire_timestamp:
            try:
                self._jwt_expire_timestamp = j.clients.itsyouonline.jwt_expire_timestamp(jwt)
            except KeyError:
                # case when jwt does not have expiration time
                pass

        if self._jwt_expire_timestamp and self._jwt_expire_timestamp - 300 < time.time():
            jwt = j.clients.itsyouonline.refresh_jwt_token(jwt, validity=3600)
            self._jwt_expire_timestamp = j.clients.itsyouonline.jwt_expire_timestamp(jwt)
            self.config.data_set('jwt_', jwt)
            self.config.save()
            self._api = None

        if self._api is None:
            self._api = Client(base_uri=self.config.data["url"])
            if self.config.data.get('god_token_'):
                header = 'Bearer %s' % self.config.data['god_token_']
                self._api.security_schemes.passthrough_client_user.set_zrobotuser_header(header)
                self._api.security_schemes.passthrough_client_admin.set_zrobotadmin_header(header)

            elif self.config.data.get('jwt_'):
                header = 'Bearer %s' % self.config.data['jwt_']
                self._api.security_schemes.passthrough_client_user.set_zrobotuser_header(header)
                self._api.security_schemes.passthrough_client_admin.set_zrobotadmin_header(header)

            if self.config.data.get('secrets_') or self.config.data.get('god_token_'):
                header = 'Bearer %s' % ' '.join(self.config.data['secrets_'])
                header += ' %s' % self.config.data.get('god_token_')
                self._api.security_schemes.passthrough_client_service.set_zrobotsecret_header(header.strip())

        return self._api

    def god_token_set(self, god_token):
        """ Add god token of robot  at client config

        Arguments:
            god_token {sting} -- god token of robot
        """
        self.config.data_set('god_token_', god_token)
        self._api = None  # force reload of the api with new god token header
