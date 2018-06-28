#!/bin/bash

set -ex

# make output directory
ARCHIVE=/tmp/archives
FLIST=/tmp/flist
mkdir -p $ARCHIVE

# install system deps
apt-get update
apt-get install -y locales git sudo python3-pip libffi-dev python3-dev libssl-dev libpython3-dev libssh-dev libsnappy-dev build-essential pkg-config libvirt-dev libsqlite3-dev -y

# setting up locales
if ! grep -q ^en_US /etc/locale.gen; then
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
    locale-gen
fi

# install jumpscale
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$DIR/../jumpscale_versions.sh"

for target in /usr/local /opt /opt/cfg /opt/code/github/jumpscale /opt/code/github/zero-os /opt/var/capnp /opt/var/log $HOME/js9host/cfg; do
    mkdir -p $target
    chown -R $USER:$USER $target
done

pushd /opt/code/github/jumpscale

# cloning source code
git clone https://github.com/jumpscale/core9
pushd core9
git checkout $CORE_REVISION
popd

git clone https://github.com/jumpscale/lib9
pushd lib9
git checkout $LIB_REVISION
popd

git clone https://github.com/jumpscale/prefab9
pushd prefab9
git checkout $PREFAB_REVISION
popd

# installing core and plugins
for target in core9 lib9 prefab9; do
    pushd ${target}
    pip3 install -e .
    popd
done
popd

cp -r /0-robot /opt/code/github/zero-os
# install 0-robot
pushd /opt/code/github/zero-os/0-robot
pip3 install -e .
popd

tar -cpzf "/tmp/archives/0-robot.tar.gz" --exclude tmp --exclude dev --exclude sys --exclude proc  /
