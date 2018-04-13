import os

from js9 import j
from zerorobot.dsl.ZeroRobotManager import ZeroRobotManager

from .ZeroRobotClient import ZeroRobotClient

JSConfigFactoryBase = j.tools.configmanager.base_class_configs


class ZeroRobotFactory(JSConfigFactoryBase):

    def __init__(self):
        self.__jslocation__ = "j.clients.zrobot"
        super().__init__(child_class=ZeroRobotClient)

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
        if ZeroRobotManager is None:
            raise RuntimeError("zerorobot library is not installed, see 'https://github.com/zero-os/0-robot' to know how to install it")
        robots = {}
        for instance in j.tools.configmanager.list(self.__jslocation__):
            robots[instance] = ZeroRobotManager(instance)
        return robots
