# Automatic syncing of data repository

The `zrobot server start` command supports automatic pushing of the data repository to backup the data to the git server.
This repository should be private as not to publish sensitive data publicly.
the git repository should also be added with it's ssh url and the robot should have a key loaded into the ssh agent that has access to that repository.

When the server is started, a greenlet is started that for each interval will commit and push the repository with the commit message `'zrobot sync'`

## Usage

```bash
zrobot server start # add flags
```

[explain flags]
