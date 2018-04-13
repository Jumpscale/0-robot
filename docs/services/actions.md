# Service actions

The services actions is the core of a service logic.
An actions is just a method on the service object.  

You can schedule action on a service using the `schedule_action` of a service. The result of the schedule_action is a `task` object.

You can inspect different properties of a task:
- **action_name**: name of the action executed by the task
- **created**: creation time of the task
- **eco**: error condition if the task ended with an exception
- **guid**: ID of the task
- **state**: state of the task. can be 'new','ok','error'
- **result**: if the task return a value, the result contains this value

## Customize actions behavior
It is possible to add some special behavior to an actions using decorators
See the API documentation for more detail: https://zero-os.github.io/0-robot/api/zerorobot/template/decorator.m.html

### Retry decorator
This decorator allows to define retry policy for the action. 
In case the action raises an exception during it's execution, the action is going to be retried according to the policy defined with the decorator arguments.

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
    @retry((RuntimeError, KeyError), tries=4, delay=3, backoff=2, logger=None)
    def foo(self):
        # some code

```

### Timeout decorator
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
    @timeout(60, error_message='Function call timed out')
    def foo(self):
        # some code

```

## Recurring actions
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

## Profile decoration
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


## Asynchronous code
Since 0-robot runs on top of gevent, you can within your templates defines some asynchronous coroutine that needs to run during the lifetime of your service.

To allow this, the TemplateBase class expose has a `gl_mgr` attribute. This is an instance of the GreenletManager class. This class let you start and managed gevent Greenlet from within your service.

As an example, let's show how we can asynchronously consume job stream for ZeroOS.
See https://github.com/zero-os/0-core/blob/master/docs/monitoring/logging.md to first understand what are job stream.

Here is the code:
```python

# this is the action that we will schedule on the service to test
def test_stream(self):
    # we start the process and keep a reference to the job
    job = self.node.client.system('top')

    # this is the callback of the stream method
    # this is where you process the data incoming from your process
    # in this case we just print 
    def cb(level, msg, flag):
        print("level %d" % level)
        print(msg)

    self._process_stream(job.id, cb)

# this method define and start the greenlet using the GreenletManager
def _process_stream(self, jobid, cb):
    def gl():
        subscriber = self.node.client.subscribe(jobid)
        subscriber.stream(cb)

    self.gl_mgr.add("jobid", gl)
    return jobid
```

The result of scheduling `test_stream` will start a `top` process on the ZeroOs node and the output of the process will be streamed back into the couroutine and printed to the logs of 0-robot.

It's important to use the Greenlet manager when you start coroutine cause 0-robot make sure that we don't leak any coroutine when deleting or updating the services.