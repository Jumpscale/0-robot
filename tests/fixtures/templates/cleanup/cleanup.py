from zerorobot.template.base import TemplateBase
from jumpscale import j


class Cleanup(TemplateBase):

    version = '0.0.1'
    template_name = "cleanup"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        self.add_delete_callback(self.cleanup1)
        self.add_delete_callback(self.cleanup2)

        self.data['output'] = j.sal.fs.getTempFileName()

    def cleanup1(self):
        self.logger.info("cleanup1")
        j.sal.fs.writeFile(self.data['output'], 'cleanup1\n', append=True)

    def cleanup2(self):
        self.logger.info("cleanup2")
        j.sal.fs.writeFile(self.data['output'], 'cleanup2', append=True)
