# ZeroRobot
[![Build Status](https://travis-ci.org/Jumpscale/zerorobot.svg?branch=master)](https://travis-ci.org/Jumpscale/zerorobot)
[![codecov](https://codecov.io/gh/Jumpscale/zerorobot/branch/master/graph/badge.svg)](https://codecov.io/gh/Jumpscale/zerorobot)

The goal of this project is to create a distributed live cycle management system.
By combining multiple ZeroRobot, each of them focusing on a specific purpose, we can create a distributed network or robot that managed nodes and applications.
The robot is responsible to orchestrate different entity that we call services. A service purpose is to model anything required to manage your IT environment.  
A service can map to something physical, like a server or an network card. Or it can model something more abstract like a virtual machine or a capacity planner.

## Concepts

### Template
A template is like is name suggest, a template for a service. In practice this is just a python class that implement some methods and have some properties.

A ZeroRobot main task is to clone the git repository where these template are and load them in memory, to they are ready to be instantiated into services.

### Service
A service is an instance of a template.  
One a service is created it can start to actually execute some actions.
The actions to be executed are ask by the user or by another service.

Each service has its own task list. This is a queue where all the required actions are stacked and processed one by one.

Some service will depend on other services to be able to complete an action. Let's call the dependent service a producer.  
When a service is asked to execute an action and requires some producer to do something for him, it will add this action to the task list of the producer.

The producer will then eventually pick the task and execute the required action. The execution of the producer's action can create a result that can be sent back to the service that ask for it.

By combining different services and actions we can create a distributed system that can scale. Also the fact that a service is only responsible for a really specific task allow to keep the code clean and concise. 

### Technically
From a technology perspective a ZeroRoot is a gevent greenlet that is responsible to answer request from users. Things like, create this service, give me the state of these services.

Each service is also running in a greenlet and is watching a queue, the task list. The services is responsible to consume all the task from it's queue to execute the action required by the user or other services. The communication between services always happens though queue. This is to ensure serialization of the action and non concurrent access to the data.

So when a service add a task to a producer's task list, it also provide a response queue on which the producer need to write to send the result of the action back to the originator service.

Each ZeroRobot also expose a REST API, to allow communication between them. So when a service ask an action to service that is managed by another robot, the request is transported though a REST call to the remote robot. All of this happens transparently for the user and it doesn't really have to know where the service is located, only that what it can provide in term of actions.