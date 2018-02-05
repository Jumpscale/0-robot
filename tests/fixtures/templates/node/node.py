from zerorobot.template.base import TemplateBase
from zerorobot.template.decorator import profile


class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    def __init__(self, name, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    @profile()
    def start(self):
        print('started')
        return 'result'

    def stop(self):
        print('stop')

    def foo(self, bar, bor=None):
        print('foo')
        return 'result'
