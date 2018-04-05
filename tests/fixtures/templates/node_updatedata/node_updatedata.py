from zerorobot.template.base import TemplateBase
from zerorobot.template.decorator import profile, timeout


class NodeUpdatedata(TemplateBase):

    version = '0.0.1'
    template_name = "node_updatedata"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def update_data(self, data):
        self.data.update(data)
