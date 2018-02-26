import cProfile
import os
import signal
import time
from functools import wraps
import gevent

from js9 import j

from .base import TemplateBase


def retry(exceptions, tries=4, delay=3, backoff=2, logger=None):
    """
    Retry calling the decorated function using an exponential backoff.

    Args:
        exceptions: The exception to check. may be a tuple of
            exceptions to check.
        tries: Number of times to try (not retry) before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Backoff multiplier (e.g. value of 2 will double the delay
            each retry).
        logger: Logger to use. If None, print.
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = '{}, Retrying in {} seconds...'.format(e, mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    gevent.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def timeout(seconds, error_message='Function call timed out'):
    """
    Raise a Timeout error if the wrapped function takes more time then seconds to execute.

    Args:
        seconds: timeout time in seconds
        error_message: message to pass to the TimeoutError exception raised
    """
    if seconds <= 0:
        seconds = None

    def deco_timout(f):
        @wraps(f)
        def f_timeout(*args, **kwargs):
            gl = gevent.spawn(f, *args, **kwargs)
            try:
                return gl.get(block=True, timeout=seconds)
            except gevent.Timeout:
                raise TimeoutError()

        return f_timeout

    return deco_timout


def profile(output=None):
    """
    Enable python cProfile for the decorated function.

    Args:
        service: service object
        output: if specified, give the path where the profile will be saved.
                if None the profile is generated into {tempdir}/zrobot_profile/{service_guid}/{function_name}-{time}.prof`

    """

    def deco_profile(f):

        @wraps(f)
        def f_profile(*args, **kwargs):
            if len(args) < 1 or not isinstance(args[0], TemplateBase):
                raise TypeError("profile decorator can only \
be used on the method of a instance of zerorobot.template.base.TemplateBase")

            service_ref = args[0]

            pr = cProfile.Profile()
            pr.enable()
            try:
                result = f(*args, **kwargs)
            finally:
                pr.create_stats()
                if output:
                    profile_path = output
                else:
                    profile_path = _temp_profile_location(service_ref.guid, f.__name__)
                pr.dump_stats(profile_path)
            return result

        return f_profile

    return deco_profile


def _temp_profile_location(guid, action):
    name = "{action}-{time}".format(
        action=action,
        time=int(time.time())
    )
    dir = os.path.join(j.dirs.TMPDIR, 'zrobot_profile', guid)
    os.makedirs(dir, exist_ok=True)
    return os.path.join(dir, name + '.prof')
