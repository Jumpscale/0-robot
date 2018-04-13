# Service state
The service state holds the information regarding the health of a service as well as some basic states.

The service state is organized per category, in each category, there can be tags and associated with a tag, a state.

So an example of a service state could be:
```
- actions
  - installed: ok
  - started: ok
- network
  - tcp-80: ok
  - tcp-8080: error
```

Category and tags can be any string. There is not restriction. But the state associated needs to be one of `'ok'`, `'error'`, `'warning'`, `'skipped'`


The service state management is completely left to the developer of the service. It is up to him to change the state a when needed.

The developer can also check the state of a another service to take decision.

See the detail API documentation about the service state for more detail about the interface: https://zero-os.github.io/0-robot/api/zerorobot/template/base.m.html#0-robot.template.base.ServiceState

Example:
```python
class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def foo(self):
        try:
            # check if the status of foo:bar is error
            self.state.check('foo','bar', 'error')
            # ....
        except StateCheckError:
            # if state is not error, StateCheckError is raised
            # .... do the work
        
        # set the state
        self.state.set('foo', 'bar', 'ok)
        # read the state
        state = self.state.get('foo','bar')
        # state variable will contain {'bar': 'ok'}

```