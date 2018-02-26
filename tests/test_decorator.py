import logging
import os
import shutil
import tempfile
import unittest

import gevent

from js9 import j
from zerorobot import config
from zerorobot.template.decorator import profile, retry, timeout
from zerorobot.template_collection import _load_template


class RetryableError(Exception):
    pass


class AnotherRetryableError(Exception):
    pass


class UnexpectedError(Exception):
    pass


class TestRetryDecorator(unittest.TestCase):

    def test_no_retry_required(self):
        self.counter = 0

        @retry(RetryableError, tries=4, delay=0.1)
        def succeeds():
            self.counter += 1
            return 'success'

        r = succeeds()

        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 1)

    def test_retries_once(self):
        self.counter = 0

        @retry(RetryableError, tries=4, delay=0.1)
        def fails_once():
            self.counter += 1
            if self.counter < 2:
                raise RetryableError('failed')
            else:
                return 'success'

        r = fails_once()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 2)

    def test_limit_is_reached(self):
        self.counter = 0

        @retry(RetryableError, tries=4, delay=0.1)
        def always_fails():
            self.counter += 1
            raise RetryableError('failed')

        with self.assertRaises(RetryableError):
            always_fails()
        self.assertEqual(self.counter, 4)

    def test_multiple_exception_types(self):
        self.counter = 0

        @retry((RetryableError, AnotherRetryableError), tries=4, delay=0.1)
        def raise_multiple_exceptions():
            self.counter += 1
            if self.counter == 1:
                raise RetryableError('a retryable error')
            elif self.counter == 2:
                raise AnotherRetryableError('another retryable error')
            else:
                return 'success'

        r = raise_multiple_exceptions()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 3)

    def test_unexpected_exception_does_not_retry(self):

        @retry(RetryableError, tries=4, delay=0.1)
        def raise_unexpected_error():
            raise UnexpectedError('unexpected error')

        with self.assertRaises(UnexpectedError):
            raise_unexpected_error()

    def test_using_a_logger(self):
        self.counter = 0

        sh = logging.StreamHandler()
        logger = logging.getLogger(__name__)
        logger.addHandler(sh)

        @retry(RetryableError, tries=4, delay=0.1, logger=logger)
        def fails_once():
            self.counter += 1
            if self.counter < 2:
                raise RetryableError('failed')
            else:
                return 'success'

        fails_once()


class TestTimeoutDecorator(unittest.TestCase):

    def test_no_timeout(self):
        self.counter = 0

        @timeout(0)
        def notimeout():
            gevent.sleep(1)
            self.counter += 1
            return 'success'

        r = notimeout()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 1)

    def test_with_timeout(self):
        self.counter = 0

        @timeout(1)
        def notimeout():
            gevent.sleep(2)
            self.counter += 1
            return 'success'

        with self.assertRaises(TimeoutError):
            r = notimeout()

        self.assertEqual(self.counter, 0)

    def test_exception(self):
        self.counter = 0

        @timeout(2)
        def with_exception():
            gevent.sleep(1)
            raise RuntimeError()
            self.counter += 1
            return 'success'

        with self.assertRaises(RuntimeError):
            r = with_exception()

        self.assertEqual(self.counter, 0)


class TestRetryTimout(unittest.TestCase):

    def test_rety_with_timeout(self):
        self.counter = 0

        @timeout(1)
        @retry(RetryableError, tries=4, delay=2)
        def fails_once():
            self.counter += 1
            if self.counter < 2:
                raise RetryableError('failed')
            else:
                return 'success'

        with self.assertRaises(TimeoutError):
            r = fails_once()

        self.assertEqual(self.counter, 1)

    def test_rety_with_timeout_too_long(self):
        self.counter = 0

        @timeout(1)
        @retry(RetryableError, tries=2, delay=0.1)
        def fails_once():
            self.counter += 1
            if self.counter < 2:
                raise RetryableError('failed')
            else:
                return 'success'

        r = fails_once()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 2)


class TestProfile(unittest.TestCase):

    def setUp(self):
        config.DATA_DIR = tempfile.mkdtemp(prefix='0robottest')

    def tearDown(self):
        if os.path.exists(config.DATA_DIR):
            shutil.rmtree(config.DATA_DIR)

    def _load_template(self, name):
        """
        name of the template to load from the
        fixtures/templates folder
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        tmpl = _load_template("https://github.com/jumpscale/0-robot",
                              os.path.join(dir_path, 'fixtures', 'templates', name))
        return tmpl

    def test_profile(self):
        Node = self._load_template('node')
        srv = Node('node1')

        srv.start()

        path = os.path.join(j.dirs.TMPDIR, 'zrobot_profile', srv.guid)
        found = j.sal.fs.listFilesInDir(path, recursive=False, filter="*.prof")
        self.assertEqual(len(found), 1, "should have found a profile in %s" % path)

    def test_only_one_service_method(self):

        @profile()
        def foo():
            pass

        with self.assertRaises(TypeError, message="should raise when applied on not service method"):
            foo()
