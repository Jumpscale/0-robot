# Getting started and Running the robot

Detailed documentation is available here [Getting Started](getting_started.md)



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
from zerorobot.template.base import TemplateBase


class Helloworld(TemplateBase):

    version = '0.0.1'
    template_name = "helloworld"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        if not self.data['msg']:
            self.data['msg'] = "Hello World"

    def echo_to_temp(self):
        j.sal.fs.writeFile("/tmp/msg.robot", self._data['msg'], append=True)
```

Let's dissect the template code a little bit

* Imports
```
from js9 import j
from zerorobot.template.base import TemplateBase
```
Because we want to use jumpscale facilities and TemplateBase as the Base class for all templates

* 
``` Template class
class Helloworld(TemplateBase):

    version = '0.0.1'
    template_name = "helloworld"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

        if not self.data['msg']:
            self.data['msg'] = "Hello World"

``` 
- name is used for service name creation
- data used to populate the `schema.capnp` data
- `self._msg` will be used through the service lifetime.


* Actions
```
    def echo_to_temp(self):
        j.sal.fs.writeFile("/tmp/msg.robot", self._data['msg'], append=True)
```
`echo_to_temp` is an action that can be scheduled
> Needs to be a method.
> ACtions can take parameter depending on the method signature.


## Creating instance of the service and schedluing actions using the DSL
using zerorobot dsl to easily interact with the robot

1- Create ZeroRobotAPI Manager
```
In [54]: from zerorobot.dsl import ZeroRobotAPI

In [55]: api = ZeroRobotAPI.ZeroRobotAPI()
```
2- Create instance of the helloworld template
```
In [58]: service = api.services.create("github.com/jumpscale/0-robot/helloworld/0.0.1", "firstservice")
Out[58]: <zerorobot.service_proxy.ServiceProxy at 0x7f71f7c392b0>

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
In [64]: service.schedule_action("echo_to_temp")

```

and if you check `/tmp/msg.robot` file you should see
```
$ cat /tmp/msg.robot
Hello World
```



## Creating instance of the service and schedluing actions using Blueprints 
* make a blueprint in some directory  `/tmp/proj/blueprints`
/tmp/proj/blueprints# cat hello.yaml 
```
services:
    - github.com/jumpscale/0-robot/helloworld/0.0.1__service4:
          msg: wilkommen

actions:
    - template: github.com/jumpscale/0-robot/helloworld/0.0.1
      service: service4
      actions: ['echo_to_temp']

```

* Connect to the robot
```
/tmp/proj/blueprints# zrobot robot connect main http://localhost:6000
[Tue30 10:35] - ConfigManager.py    :107 :j                              - INFO     - found jsconfig dir in: /opt/code/config_test
Connection to main saved

```

* Execute the blueprint
`zrobot blueprint execute hello.yaml`

```
/tmp/proj/blueprints# zrobot blueprint execute hello.yaml 
[Tue30 10:51] - ConfigManager.py    :107 :j                              - INFO     - found jsconfig dir in: /opt/code/config_test
blueprint executed

```