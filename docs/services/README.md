# Services

- [Service data](#service-data)
- [Service state](#service-state)
- [Service Actions](#service-actions)

## Service data
The services data is the information that a service needs to receive to be created and the information the services gather during its lifetime. The data of a service is always private and is never going to be shared with another service or client. The service itself is the only one to have access to its data.

The definition of which data needs to be given is specified in the template schema. This schema is a capnp object, in which we define the data of the services.

Example of a schema:
```capnp
@0xc5ba0f64c9013a79;

struct Schema {
    id @0: Text; # mac address of the mngt network card
    hostname @1: Text;

    redisAddr @2 :Text; # redis addr for client
    redisPort @3 :UInt32 = 6379; # redis port for client
    redisPassword @4 :Text; # redis password for client
    version @5 :Text;
}
```

From within a service, you can access it with the `data` attribute of the service class. This attribute is a dictionary that maps to the definition of the schema. Trying to access key that are not defined in the schema, will raise an exception.

example:
```python
class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    def foo(self):
        # access the data of the service
        print(self.data['hostname'])
        # update the data of the service
        self.data['version'] = "1.1.1"
        # this line will raise
        self.data['randomkey'] = 'value'
```

### Update data from blueprint
When you send a blueprint that contains the definition of service that already exists. 
The data from the blueprint will be proposed to the service. The service can then decide what to do with the new data.
The writer of the service template must implement the method `update_data`:

example:
```python
class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

     def update_data(self, d):
        # foo is a field that can't be updated
        # so we remove it from the proposed data
        if 'foo' in d:
            del ['foo']
        
        # then merge the rest of the data
        self.data.update(d)
        
        # you can also add logic according
        # to the data you update
        self.reconnect_client()
        # you probably want to save this state now
        self.save()
```

## Service state
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

Category and tags can be any string. There is not restriction. But the state associated needs to be one of `'new'`, `'ok'` or `'error'`


The service state management is completely left to the developer of the service. It is up to him to change the state a when needed.

The developer can also check the state of a another service to take decision.

See the detail API documentation about the service state for more detail about the interface: https://jumpscale.github.io/0-robot/api/0-robot/template/base.m.html#0-robot.template.base.ServiceState

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
## Service actions

The services actions is the core of a service logic.
An actions is just a method on the service object.

### Customize actions behavior
It is possible to add some special behavior to an actions using decorators
See the API documentation for more detail: https://jumpscale.github.io/0-robot/api/0-robot/template/decorator.m.html

#### Rety decorator
This decorator allows to define retry policy for the action. 
In case the action raises an exception during it's execution, the action is going to be retied according to the policy defined with the decorator arguments.

Arguments of the decorator:
- exceptions: The exception to check. may be a tuple of exceptions to check.
- tries: Number of times to try (not retry) before giving up. 
- delay: Initial delay between retries in seconds. 
- backoff: Backoff multiplier (e.g. value of 2 will double the delay each retry). 
- logger: Logger to use. If None, print.

```python
from zerorobot.template.decorator import retry

class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    # retry the method when the exception is RuntimeError or KeyError
    # it will wait 3, 6, 12, 16 seconds before raising the exception
    def retry((RuntimeError, KeyError), tries=4, delay=3, backoff=2, logger=None):
    def foo(self):
        # some code

```


#### Timeout decorator
This decorator allow to set a maximum execution time for an action. It will raise a `TimeoutError` if the wrapped action takes more time then the timeout value to execute.

Arguments of the decorator:
- seconds: timeout time in seconds 
- error_message: message to pass to the TimeoutError exception raised

```python
from zerorobot.template.decorator import timeout

class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    # set the timeout of the method to 60 second.
    # and set a custom error message
    @timeout(60, error_message='Function call timed out'):
    def foo(self):
        # some code

```

### Recurring actions
It is also possible to have some action be recurring. Which means these action are going to be scheduled every X seconds.
This is useful for some actions that monitor the state or some cleanup actions for examples.

In order to make an action recurring you need to use the `recurring_action` method present on TemplateBase and thus in all your services.

`recurring_action` takes 2 parameters; action and period:
- action: Is the action you want to make recurring, it can be given as a reference to the method itself, or as a string being the name of the action.  
- period is the recurring period in second (can be a floating number) 

Since we don't have control over how long other tasks from the task list takes. We can only ensure that the action is never going to be scheduled faster then every period second. That means that it can be a longer time then period second during which the action is not executed.

Example:
```python
class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        # using the reference to the method
        self.recurring_action(self.foo, 10)
        # using the name of the method
        self.recurring_action("foo", 10)

    def foo(self):
        # code of the recurring action goes here.
        # ...

```

### Profile decoration
During the development of your services, you might want to profile some action 
to analyse how they performs. This decorator allow you gather profiling information about a method.  
It uses cProfile under the hood. By default the result of the profile are stored on your filesystem at `/tmp/zrobot_profile/{service_guid}/{function_name}-{time}.prof`, 
but you can overwrite the destination with the `output` parameter of the decorator

Example:
```python
class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)
        # using the reference to the method
        self.recurring_action(self.foo, 10)
        # using the name of the method
        self.recurring_action("foo", 10)

    # enable profiling for method foo and store result in /tmp/profile1
    @profile(output='/tmp/profile1')
    def foo(self):
        # some performance sensitive code
        # ...

```