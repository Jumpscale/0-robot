from zerorobot.template.base import TemplateBase
from zerorobot.template.decorator import profile, timeout


class Validate(TemplateBase):

    version = '0.0.1'
    template_name = "validate"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def validate(self):
        if not self.data.get('required'):
            raise ValueError("required need to be specified in the data")
