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
  -L, --listen TEXT         listen address (default :6600)
  -D, --data-repo TEXT      URL of the git repository where to save the data
                            of the zero robot  [required]
  -T, --template-repo TEXT  list of template repository URL
  -R, --robots TEXT         address of reachable robots
  --help                    Show this message and exit.
```
Options details:

- `--listen`: The interface and port on which the robot REST API need to listen to. Has to be under the form `host:port`  
e.g: `0.0.0.0:8080`
- `--data-repo`: The URL of a git repository where the data of your services will be stored. When starting, the robot also loads all the services present in this repository.
This parameter is required for the robot to starts.
- `--temlate-repo` The URL of a repository that contains templates. You can give multiple template repository by give multiple time the parameter.
- `--robots` The URL of any other robots that needs to be reachable from this robot. You can give multiple robot URL by give multiple time the parameter.

### example:
```bash
zrobot server start --listen :6601 --template-repo https://github.com/jumpscale/0-robot.git --data-repo https://github.com/user/zrobot1.git --robots http://localhost:6602
```