# Getting started

## Install 0-Robot
Requirements: You need to have [Jumpscale9](https://github.com/jumpscale/home) installed to be able to run the 0-Robot.  
See the [intallation instruction](https://github.com/Jumpscale/core9#jumpscale-9)

Notes:
If https://github.com/Jumpscale/core9/issues/226 issue still open, you need to install `psutil` version 5.4.3 or above prior installing `jumpscale/core9 above`

Clone this repository and install the zerorobot:

```bash
apt-get install -y libsqlite3-dev
git clone https://github.com/zero-os/0-robot.git
cd 0-robot
mkdir -p /opt/code/github/zero-os/0-robot
cp -a * /opt/code/github/zero-os/0-robot/
pip install .
```



## Start the robot:
```
Usage: zrobot server start [OPTIONS]

  start the 0-robot daemon. this will start the REST API on address and port
  specified by --listen and block

Options:
  -L, --listen TEXT             listen address (default :6600)
  -D, --data-repo TEXT          URL of the git repository or absolute path
                                where to save the data of the zero robot
  -T, --template-repo TEXT      list of template repository URL. Use fragment
                                URL to specify a branch:
                                http://github.com/account/repo#branch
  -C, --config-repo TEXT        URL of the configuration repository (https://g
                                ithub.com/Jumpscale/core9/blob/development/doc
                                s/config/configmanager.md)
  -K, --config-key TEXT         Absolute path to ssh key to secure
                                configuration data, which is committed and
                                pushed (see auto-push) in the configuration
                                repo. If omitted, the robot will try to use
                                the key configured key in jumpscale if any or
                                will generate a new ssh key.
  --debug                       enable debug logging
  --telegram-bot-token TEXT     Bot to push template action failures
  --telegram-chat-id TEXT       Chat id to push template action failures
  --auto-push                   enable automatically commit and pushing of
                                data repository
  --auto-push-interval INTEGER  interval in minutes of automatic pushing of
                                data repository
  --organization TEXT           if specified, enable JWT authentication for
                                each request.
  --help                        Show this message and exit.

```
Options details:

- `--listen`: The interface and port on which the robot REST API need to listen to. Has to be under the form `host:port`  
e.g: `0.0.0.0:8080`
- `--data-repo`:  
The URL of a git repository or the absolute path of a directory on the local file system where the data of your services will be stored  
if not specified, a directory is automatically created `{j.dirs.DATADIR}/zrobot`  
When starting, the robot also loads all the services present in this repository.  
- `--template-repo`:  
The URL of a repository that contains templates. You can give multiple template repository by give multiple time the parameter.
if the url contains a fragment (#) the fragment is used as branch name. example: http://github.com/account/repo#mybranch will use the 'mybranch` branch
- `--config-repo`:  
URL or absolute path of the configuration repository.  
 if not specified and jumpscale doens't have a configuration repo already configure a directory is automatically created in `{j.dirs.CODEDIR}/local/stdorg/config`
 otherwise the robot uses the configuration from jumpscale
 - `--config-key`: 
Absolute path to ssh key to secure configuration data, which is committed and pushed (see auto-push) in the configuration repo. If omitted, the robot will try to use the key configured key in jumpscale if any or will generate a new ssh key.
- `--debug`:  
Sets the logger output level to debug
- `auto-push`:  
Enables automatic commiting and pushing of the data repository for backup. Check the [automatic syncing chapter](#automatic-syncing-of-data-repository) for more details
- `--auto-push-interval`:  
Define a custom interval in minutes for `auto-push` if enabled (default: 60)

### example:
```bash
zrobot server start --listen :6601 --template-repo https://github.com/zero-os/0-robot.git --data-repo https://github.com/user/zrobot1.git --robots http://localhost:6602 --organization myOrg
```

## Running 0-robot in a docker

0-robot is available as a published docker image on docker hub: [https://hub.docker.com/r/jumpscale/0-robot/](https://hub.docker.com/r/jumpscale/0-robot/)

To run it:
- mount the password-less id_rsa named ssh key into /root/.ssh. Make sure id_rsa is the only ssh key that is mounted into /root/.ssh
- expose the 0-robot listening port 
- pass the 0-robot arguments as environment variables

eg:
```bash
root@myawesomemachine:~# docker run --name 0-robot -d -p 192.168.199.2:6600:6600 -v /root/.ssh2:/root/.ssh -e data-repo=ssh://git@myawesomegitserver.org:10023/MyAwesomeOrganization/myawseomedatarepo.git -e config-repo=ssh://git@myawesomegitserver.org:10023/MyAwesomeOrganization/myawseomeconfigrepo.git -e config-key=/root/.ssh/id_rsa -e template-repo=https://github.com/zero-os/0-templates.git jumpscale/0-robot:latest
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
