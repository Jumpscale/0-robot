from zerorobot.template.base import TemplateBase
from zerorobot.template.decorator import profile, timeout


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

    def fookwargs(self, bar, **kwargs):
        return kwargs

    @property
    def bar(self):
        # raise here so we can test that it doesn't
        # fail when trying to list actions
        raise RuntimeError()

    @timeout(10)
    def error(self):
        raise RuntimeError('this is an error')

    def test_return(self, return_val):
        return return_val
