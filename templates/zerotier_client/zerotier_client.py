from js9 import j

from zerorobot.template.base import TemplateBase


class ZerotierClient(TemplateBase):

    version = '0.0.1'
    template_name = "zerotier_client"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        # client instance already exists
        if self.name in j.clients.zerotier.list():
            return

        # create the client instance
        token = self.data.get('token')
        if not token:
            raise RuntimeError("no token specified in service data")

        # this will create a configuration for this instance
        _ = j.clients.zerotier.get(self.name, data={'token_': self.data['token']})

    def delete(self):
        """
        delete the client configuration
        """
        j.clients.zerotier.delete(self.name)
