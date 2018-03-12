import unittest

import zerorobot.errors as errors
from zerorobot.template.state import StateCheckError

class TestExceptions(unittest.TestCase):
    def setup(self):
        pass

    def test_expected_error(self):
        tt = [
            {
                'error': ValueError(),
                'expected': False,
                'msg': 'ValueError is an unexpected error',
            },
            {
                'error': RuntimeError(),
                'expected': False,
                'msg': 'RuntimeError is an unexpected error',
            },
            {
                'error': StateCheckError(),
                'expected': True,
                'msg': 'StateCheckError is an expected error',
            },
        ]

        for tc in tt:
            result = isinstance(tc['error'], errors.ExpectedError)
            self.assertEqual(result, tc['expected'], tc['msg'])
            
