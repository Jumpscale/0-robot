import collections
import os

from jumpscale import j
from zerorobot.dsl.ZeroRobotManager import ZeroRobotManager

from .ZeroRobotClient import ZeroRobotClient

JSConfigFactoryBase = j.tools.configmanager.base_class_configs


class ZeroRobotFactory(JSConfigFactoryBase):

    def __init__(self):
        self.__jslocation__ = "j.clients.zrobot"
        super().__init__(child_class=ZeroRobotClient)
        self._robots = RobotLoader()

    def generate(self):
        """
        generate the client out of the raml specs
        """
        path = j.sal.fs.getDirName(os.path.abspath(__file__)).rstrip("/")
        c = j.tools.raml.get(path)
        # c.specs_get('https://github.com/Jumpscale/0-robot/blob/master/raml')
        c.client_python_generate()

    @property
    def robots(self):
        """
        list all the ZeroRobot accessible
        return a dictionary with
        key = instance name of the 0-robot
        value: ZeroRobotManager object

        ZeroRobotManager is a high level client for 0-robot that present the 0-robot API with an easy interface
        see https://zero-os.github.io/0-robot/api/zerorobot/dsl/ZeroRobotManager.m.html for full API documentation
        """
        return self._robots


class RobotLoader(collections.MutableMapping):

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        raise NotImplementedError("you cannot set a robot.")

    def __delitem__(self, key):
        j.clients.zrobot.delete(key)

    def __iter__(self):
        return iter(j.clients.zrobot.getall())

    def __len__(self):
        return j.clients.zrobot.count()

    def __keytransform__(self, key):
        return key

    def get(self, key):
        if not isinstance(key, str):
            raise TypeError

        if not j.clients.zrobot.exists(key):
            raise KeyError()

        return ZeroRobotManager(key)

    def __repr__(self):
        robots = {}
        for instance in j.clients.zrobot.list():
            robots[instance] = ZeroRobotManager(instance)
        return str(robots)

    __str__ = __repr__
