# Template

A template is the source of a service.  
It contains the definition of the [actions](../../glossary.md#action), the configuration and the data schema of a [service](../../glossary.md#service).

## Template Unique Identifier (template UID)
A template is identified by the url of the git repository it comes from.  
There is different information extracted from the URL:
- the host
- the account
- the repository name
- the name of the template itself
- a version

e.g: github.com/jumpscale/0-robot/node/1.0.0 would result into
```
host: github.com
account: jumpscale
repository name: 0-robot
template name: node
version: 1.0.0
```

When creating a new service, the user needs to refer to the template used with its template UID.

This snippet of code show how to create a new service using a template UID:
```python
from zerorobot import template_collection as tcol

template_uid = "github.com/jumpscale/0-robot/node/1.0.0"
name = "container1"
args = {'foo': 'bar'}
container = tcol.instantiate_service(template_uid, name, args)
```

## How to create a new template
A template is composed of two files, a capnp schema and a python class that inherits `zerorobot.template.base.TemplateBase`

These two files needs to be in a directory that is named after the template name.

This is a tree of a templates repository with a single template called node.

```
templates
├── node
│   ├── node.py
│   └── schema.capnp
```

The name of the template class needs to be the name of the template capitalized. So for a template `node`, the class needs to be called `Node`.

### Minimal code:

python class:
```python
from zerorobot.template.base import TemplateBase


class Node(TemplateBase):
    # define the verion of this template
    version = '0.0.1'
    template_name = "node"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
```
capnp schema:
```capnp
# this id needs to be unique per template
@0xc5ba0f64c9013a79;

struct Schema {
    # here we define the service data of the template
}
```
