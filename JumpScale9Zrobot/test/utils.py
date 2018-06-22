import os
import shutil
import tempfile
from unittest import TestCase
from unittest.mock import MagicMock

from zerorobot import config, template_collection
from zerorobot.template_uid import TemplateUID


class ZrobotBaseTest(TestCase):

    @classmethod
    def preTest(cls, path, template):
        config.data_repo = config.DataRepo(tempfile.mkdtemp(prefix='0-templates_'))
        template_collection._load_template('https://github.com/zero-os/0-templates', path)
        template.template_uid = TemplateUID.parse(
            'github.com/zero-os/0-templates/%s/%s' % (template.template_name, template.version))

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(config.data_repo.path):
            shutil.rmtree(config.data_repo.path)


def task_mock(result):
    task = MagicMock()
    task.wait = MagicMock(return_value=task)
    task.result = result
    return task


def mock_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
