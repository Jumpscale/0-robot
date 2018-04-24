# 0-Robot

**master:**   
[![Build Status](https://travis-ci.org/zero-os/0-robot.svg?branch=master)](https://travis-ci.org/zero-os/0-robot)
[![codecov](https://codecov.io/gh/zero-os/0-robot/branch/master/graph/badge.svg)](https://codecov.io/gh/zero-os/0-robot)  
**development:**  
[![Build Status](https://travis-ci.org/zero-os/0-robot.svg?branch=development)](https://travis-ci.org/zero-os/0-robot)
[![codecov](https://codecov.io/gh/zero-os/0-robot/branch/development/graph/badge.svg)](https://codecov.io/gh/zero-os/0-robot)

The goal of this project is to create a distributed live cycle management system.
By combining multiple 0-Robots, each of them focusing on a specific purpose. We can create a distributed network of robots that manages nodes and applications.
A robot is responsible for orchestrating different entities that we call 'services'. A service's purpose is to model anything required to manage your IT environments.  
A service can map to something physical, like a server or an network card, or it can model something more abstract like a virtual machine or a capacity planner.

## [Documentations](docs)
- [Concepts](docs/concepts.md)
- [Getting started](docs/getting_started.md)
- [Glossary](docs/glossary.md)
- Components:
    - [Templates](docs/templates/README.md)
    - [Services](docs/services/README.md)
## API documentation
See https://zero-os.github.io/0-robot/api/zerorobot/index.html


## Migration
If you update from 0.5.x to >=0.6.x, check the migration documentation: [0.5_to_0.6.md](docs/migrations/0.5_to_0.6.md)