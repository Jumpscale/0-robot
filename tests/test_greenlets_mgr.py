import unittest

import gevent
from zerorobot.template.base import GreenletsMgr


class TestGreenletsMgr(unittest.TestCase):

    def foo(self):
        print("hello")

    def test_create(self):
        mgr = GreenletsMgr()
        self.assertEqual(mgr.gls, {})

    def test_add_get(self):
        mgr = GreenletsMgr()

        tt = ["string", 1, 1.0, None]
        for tc in tt:
            with self.assertRaises(TypeError, msg="should accept only instance of gevent.Greenlet or callable, not %s" % type(tc)):
                mgr.add("key", tc)

        # add greenlet created with spawn
        gl = gevent.spawn(self.foo)
        mgr.add("foo", gl)
        self.assertEqual(mgr.gls["foo"], gl)

        # add Greenlet object
        gl = gevent.Greenlet(run=self.foo)
        mgr.add("foo", gl)

        # add method
        mgr.add("foo", self.foo)

        # add function
        def bar():
            pass
        mgr.add("foo", bar)

        with self.assertRaises(KeyError, msg='should raise KeyError if try to get non existing gl'):
            mgr.get('nonexists')

    def test_stop(self):
        mgr = GreenletsMgr()
        mgr.add("foo", gevent.spawn(self.foo))
        mgr.stop('foo')
        gl = mgr.get('foo')
        self.assertFalse(gl.started)
        self.assertTrue(gl.ready())

        # should not raise is we try to stop a non existing greenlet
        mgr.stop("nonexists")
