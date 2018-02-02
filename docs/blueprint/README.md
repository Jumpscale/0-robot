# Blueprint

A blueprint is a description of which [service](#service-block) needs to be created and which [action](#action-block) needs to executed. 
It's written in yaml.

A blueprint can be decomposed into 2 types of blocks, service block and action block.

## Service block
This is where you describe what service you want to create or update. This block is identify with the key `services` and contains a list of service description.

If you create multiple service in one blueprint, and one service depend on another one, make sure to put the required service upper in the service list so it's created before and available for other service to use.

A service description is formed with :
- the uid of template to use and the name of the service joined with a double underscore.
- the data of the service

example of a valid service description:
```yaml
github.com/jumpscale/0-robot/node/0.0.1__node1:
    foo: bar
```
    

## Action block
This is where you schedule service actions.  
The action block is identify with the key `actions` and contain a list of action description.

An action description is formed with:
- template uid
- name of a service
- list of action name
- arguments of the action

Only the list of action is required, template uid and service name can be omitted. 
I only template uid is specified, the actions will be schedule on all the service of this type.
If only the name of the service is specified, the actions will be schedule only the service with this name.
If arguments is specified, the argument dictionary will be passed to the action.

examples of a valid action blocks:
```yaml
# only actions, will schedule install and start action on all services
actions: ['install', 'start']
```

```yaml
# actions and template, will schedule install and start action on all services of type `github.com/jumpscale/0-robot/node/0.0.1`
template: github.com/jumpscale/0-robot/node/0.0.1
actions: ['install', 'start']
```

```yaml
# actions and service name, will schedule install and start action on all services with name 'node1'
name: node1
actions: ['install', 'start']
```


```yaml
# full block, will schedule install and start action on service type `github.com/jumpscale/0-robot/node/0.0.1` and with name 'node1'
template: github.com/jumpscale/0-robot/node/0.0.1
name: node1
actions: ['install', 'start']
```

```yaml
# full block with argument, will schedule 'migrate_vm' action and pass the argument 'destination' to the 'migrate_vm' action.
template: github.com/jumpscale/0-robot/node/0.0.1
name: node1
actions: ['migrate_vm']
args:
    destination: node2
```

## Full example:
This blueprint will  create 2 new node services and schedule `install` and `start` action on both of them.
```yaml
services:
    - github.com/jumpscale/0-robot/node/0.0.1__node1:
        foo: bar
    
    - github.com/jumpscale/0-robot/node/0.0.1__node2:
        foo: bar

actions:
    template: github.com/jumpscale/0-robot/node/0.0.1
    actions: ['install', 'start']
```