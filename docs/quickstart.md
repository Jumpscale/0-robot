# Installation
```
git clone https://github.com/Jumpscale/0-robot/
cd 0-robot
pip3 install -r requirements.txt
python3 setup.py install

```
> checkout to branch package if you face any problems

# Running tests
```
 pip3 install codecov
./utils/scripts/jumpscale_install.sh
./tests/prepare_env.sh
make test
```


# Running the robot
* `zrobot server start -L :6600 -T https://github.com/jumpscale/0-robot.git -D https://github.com/xmonader/zdata --debug`
```
-T is used for template repos
-D is used for 0-robot data repo
--debug to see more logs for inspection
```


# Hello world template/service

Our service will be responsible just for one task; writing a message in a file `/tmp/msg.robot`
Let's see how can we do that

First, we need to think what kind of data that service will require? it will need a `msg` to be written in the file and maybe the filename can be customized as well instead of just `/tmp/msg.robot`

Let's get to creating the `template` templates are like "classes" and services are like "objects" created from these classes

```
├── helloworld
│   ├── helloworld.py
│   ├── schema.capnp
```
> Templates are contained in a directory with a python file with the same name and capnp format file to describe the data.


The whole thing
- `schema.capnp`
```
@0x8ee99b43f92f8c51;

struct Schema {
    msg @0: Text;
}
```
> 

- `helloworld.py`
```
from js9 import j
from zerorobot.template.base import TemplateBase

HELLOWORLD_TEMPLATE_UID = "github.com/jumpscale/0-robot/helloworld/0.0.1"


class Helloworld(TemplateBase):

    version = '0.0.1'
    template_name = "helloworld"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        if not self.data['msg']:
            self.data['msg'] = "Hello World"

        self._msg = self.data['msg']

    def echo_to_temp(self):
        with open("/tmp/msg.robot", "a") as f:
            f.write(self._msg)


```

Let's dissect the template code a little bit

* Imports
```
from js9 import j
from zerorobot.template.base import TemplateBase
```
Because we want to use jumpscale facilities and TemplateBase as the Base class for all templates

* Template UID (Unique ID for the template)
```
HELLOWORLD_TEMPLATE_UID = "github.com/jumpscale/0-robot/helloworld/0.0.1"
```
* 
``` Template class
class Helloworld(TemplateBase):

    version = '0.0.1'
    template_name = "helloworld"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        if not self.data['msg']:
            self.data['msg'] = "Hello World"

        self._msg = self.data['msg']
``` 
- name is used for service name creation
- data used to populate the `schema.capnp` data
- `self._msg` will be used through the service lifetime.


* Actions
```
    def echo_to_temp(self):
        with open("/tmp/msg.robot", "a") as f:
            f.write(self._msg)

```
`echo_to_temp` is an action that can be scheduled. (also it can take parameters.) 
> Needs to be a method.



## Creating instance of the service
using zerorobot dsl to easily interact with the robot

1- Create ZeroRobotAPI Manager
```
In [54]: from zerorobot.dsl import ZeroRobotAPI

In [55]: api = ZeroRobotAPI.ZeroRobotAPI()
```
2- Create instance of the helloworld template
```
In [58]: api.services.create("github.com/jumpscale/0-robot/helloworld/0.0.1", "firstservice")
Out[58]: <zerorobot.service_proxy.ServiceProxy at 0x7f71f7c392b0>

In [59]: service = _
```

you can use services.names dict to retrieve service by itsname
```
In [60]: api.services
Out[60]: <zerorobot.dsl.ZeroRobotAPI.ServicesMgr at 0x7f71f7ea4f60>

In [61]: api.services.names
Out[61]: 
{'firstservice': <zerorobot.service_proxy.ServiceProxy at 0x7f71f7c5a470>,
 'hi1': <zerorobot.service_proxy.ServiceProxy at 0x7f71f7c39358>,
 'hi2': <zerorobot.service_proxy.ServiceProxy at 0x7f71f7c5a240>}



In [63]: api.services.names['firstservice']
Out[63]: <zerorobot.service_proxy.ServiceProxy at 0x7f71f7c28470>
```

Now let's ask the service to execute its specific task `echo_to_temp`
```
In [64]: s.schedule_action("echo_to_temp")

```

and if you check `/tmp/msg.robot` file you should see
```
$ cat /tmp/msg.robot
Hello World
```