#!/bin/bash

set -ex

# make output directory
ARCHIVE=/tmp/archives
FLIST=/tmp/flist
mkdir -p $ARCHIVE

apt-get update
apt-get install -y git sudo python3-pip

pip3 install --upgrade pip

# install jumpscale
export BRANCH="development"

for target in /usr/local /opt /opt/cfg /opt/code/github/jumpscale /opt/code/github/zero-os /opt/var/capnp /opt/var/log $HOME/js9host/cfg; do
    mkdir -p $target
    chown -R $USER:$USER $target
done


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

cp -r /0-robot /opt/code/github/zero-os
# install 0-robot
pushd /opt/code/github/zero-os/0-robot
pip3 install -r requirements.txt
pip3 install -e .
cp utils/scripts/autobuild/startup.toml /.startup.toml
popd

tar -cpzf "/tmp/archives/0-robot.tar.gz" --exclude tmp --exclude dev --exclude sys --exclude proc  /