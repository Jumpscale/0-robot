# Automatic syncing of data repository

The `zrobot server start` command supports automatic pushing of the data repository to backup the data to the git server.
This repository should be private as not to publish sensitive data publicly.
The git repository should also be added with it's ssh url. Zrobot assumes that the ssh key set in the config repo has access to the data repository.

When the server is started, a greenlet is started that for each interval will commit and push the repository with the commit message `'zrobot sync'`

## Usage

```bash
zrobot server start # add flags
```

[explain flags]
