#!/bin/bash
set -e

sudo chown $USER:$USER /opt/
sudo chown -R $USER:$USER /usr/local

# settings
export BRANCH="master"

mkdir -p /opt/code/github/jumpscale
pushd /opt/code/github/jumpscale


# cloning source code
for target in core9 lib9; do
    git clone --depth=1 -b ${BRANCH} https://github.com/jumpscale/${target}
done

# installing core and plugins
for target in core9 lib9; do
    pushd ${target}
    pip3 install .
    popd
done

popd