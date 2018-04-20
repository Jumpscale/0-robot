import unittest

from js9 import j
from zerorobot.server.auth import user_jwt


class TestJWT(unittest.TestCase):

    def test_create_decode(self):
        key = j.data.idgenerator.generateXCharID(256)
        claims_input = {"service_guid": "12345"}
        token = user_jwt.create(claims_input)

        claims_output = user_jwt.decode(token)
        assert claims_input == claims_output

    def test_verify(self):
        key = j.data.idgenerator.generateXCharID(256)
        claims_input = {"service_guid": "12345"}
        token = user_jwt.create(claims_input)

        claims_output = user_jwt.decode(token)
        assert user_jwt.verify('12345', token)
        assert not user_jwt.verify('12345', '0000'), "wrong token should return False"
        assert not user_jwt.verify('0000', token), "wrong service guid should return False"
        assert not user_jwt.verify('12345', None), "no token should return false"
        assert not user_jwt.verify('12345', ''), "no token should return false"
