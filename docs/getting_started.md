# Getting started

## Install 0-Robot
Requirements: You need to have [Jumpscale9](https://github.com/jumpscale/home) installed to be able to run the 0-Robot.  
See the [intallation instruction](https://github.com/Jumpscale/core9#jumpscale-9)

Clone this repository and install the zerorobot:

```bash
git clone https://github.com/Jumpscale/0-robot.git
cd 0-robot
pip install .
```
## Start the robot:
```
zrobot server start --help
Usage: zrobot server start [OPTIONS]

  start the 0-robot daemon. this will start the REST API on address and port
  specified by --listen and block

Options:
  -L, --listen TEXT             listen address (default :6600)
  -D, --data-repo TEXT          URL of the git repository where to save the
                                data of the zero robot  [required]
  -T, --template-repo TEXT      list of template repository URL
  -C, --config-repo TEXT        URL of the configuration repository (https://g
                                ithub.com/Jumpscale/core9/blob/development/doc
                                s/config/configmanager.md)
  --debug                       enable debug logging
  --auto-push                   enable automatically commit and pushing of
                                data repository
  --auto-push-interval INTEGER  interval in minutes of automatic pushing of
                                data repository
  --help                        Show this message and exit.
```
Options details:

- `--listen`: The interface and port on which the robot REST API need to listen to. Has to be under the form `host:port`  
e.g: `0.0.0.0:8080`
- `--data-repo`: The URL of a git repository where the data of your services will be stored. When starting, the robot also loads all the services present in this repository.
This parameter is required for the robot to starts.
- `--template-repo` The URL of a repository that contains templates. You can give multiple template repository by give multiple time the parameter.
- `--config-repo` URL of the configuration repository. This option is added to run 0-robot in a container (eg docker, core-0)
- `--debug`: Sets the logger output level to debug
- `auto-push`: Enables automatic commiting and pushing of the data repository for backup. Check the [automatic syncing chapter](#automatic-syncing-of-data-repository) for more details
- `--auto-push-interval` Define a custom interval in minutes for `auto-push` if enabled (default: 60)

## Running 0-robot in a docker

0-robot is available as a published docker image on docker hub: [https://hub.docker.com/r/jumpscale/0-robot/](https://hub.docker.com/r/jumpscale/0-robot/)

To run it:
- put the password-less ssh keys that have access to data, template & config repositories into a directory, and mount it into the docker image on `/root/.ssh`
- expose the 0-robot listening port 

eg:
```bash
root@myawesomemachine:~# docker run --name 0-robot -d -p 192.168.199.2:6600:6600 -v /root/.ssh2:/root/.ssh jumpscale/0-robot:latest zrobot server start -D ssh://git@myawesomegitserver.org:10023/MyAwesomeOrganization/myawseomedatarepo.git -C ssh://git@myawesomegitserver.org:10023/MyAwesomeOrganization/myawseomeconfigrepo.git -T https://github.com/zero-os/0-templates.git
```

### example:
```bash
zrobot server start --listen :6601 --template-repo https://github.com/jumpscale/0-robot.git --data-repo https://github.com/user/zrobot1.git --robots http://localhost:6602
```

## Automatic syncing of data repository

The `zrobot server start` command supports automatic pushing of the data repository to backup the data to the git server.
This repository should be private as not to publish sensitive data publicly.
The repository should also be added with it's **ssh url** (to the origin remote) for the automatic pushing to work. 0-Robot assumes that the ssh key set in the config repo has access to the data repository (key provided when calling `js9_config init` in the config repository).

When the server is started, a greenlet is started that for each interval will commit and push the repository with the commit message `'zrobot sync'` if there are any changes since the last push.

### example:
```bash
zrobot server start -D git@github.com:user/zrobot-data.git -C git@github.com:user/zrobot-config.git -T git@github.com:openvcloud/0-templates.git --auto-push --auto-push-interval 120
```

This call of zrobot server start would enable auto pushing of the data repository (git@github.com:user/zrobot-data.git) every 120 minutes.
Omitting `--auto-push-interval 120` will push the repository every 60 minutes.
