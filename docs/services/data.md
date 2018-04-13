# Service data
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

## Validate service data received during creation
Usually you want to validate the data that your service received when it is created.
To do that, the TemplateBase class allow you to overwrite the `validate` method and implement all your validation logic inside. The `validate` method is automatically called after your service is instantiated and also when you service is reloaded after the robot is restared.

example of data validation:
 ```python
class Node(TemplateBase):

    version = '0.0.1'
    template_name = "node"

    def __init__(self, name=None, guid=None, data=None):
        super().__init__(name=name, guid=guid, data=data)

    # this method is automatically called after the __init__ method
    def validate(self):
        # ensure that the data received is correct
        if 'hostname' not in self.data:
            raise ValueError("service can't be created without hostname")
```

> What happens if some of some of my services raise an exception while executing the `validate` action when the robot is starting?

In that case, the services that fails to load properly will be kept in a list and the robot will continue his life. This is done so we don't block a robot if
some service fail to load because of some remote dependencies that can't be found for some reason for example.

The list of failed service is then passed to a greenlet that will try to re-execute the `validate` function forever.
While the service is in this state, it will **not** process the tasks in its task list. Reason is the behavior would be unpredictable since something is wrong with the service in the first place.
As soon as the `validate` method passes, the service is remove from the list and start processing his task list.

When all the service have been removed from the list, the greenlet exists.



## Update data from blueprint
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

     def update_data(self, data):
        # foo is a field that can't be updated
        # so we remove it from the proposed data
        if 'foo' in data:
            del ['foo']
        
        # then merge the rest of the data
        self.data.update(data)
        
        # you can also add logic according
        # to the data you update
        self.reconnect_client()
        # you probably want to save this state now
        self.save()
```