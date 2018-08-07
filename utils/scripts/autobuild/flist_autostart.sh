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
export CORE_REVISION="development"
export LIB_REVISION="development"
export PREFAB_REVISION="development"

for target in /usr/local /opt /opt/cfg /opt/code/github/threefoldtech /opt/var/capnp /opt/var/log $HOME/jumpscale/cfg; do
    mkdir -p $target
    chown -R $USER:$USER $target
done

pushd /opt/code/github/threefoldtech

# cloning source code
git clone https://github.com/threefoldtech/jumpscale_core
pushd jumpscale_core
git checkout $CORE_REVISION
popd

git clone https://github.com/threefoldtech/jumpscale_lib
pushd jumpscale_lib
git checkout $LIB_REVISION
popd

git clone https://github.com/threefoldtech/jumpscale_prefab
pushd jumpscale_prefab
git checkout $PREFAB_REVISION
popd


# installing core and plugins
for target in jumpscale_core jumpscale_lib jumpscale_prefab; do
    pushd ${target}
    pip3 install -e .
    popd
done
popd

cp -r /0-robot /opt/code/github/threefoldtech
# install 0-robot
pushd /opt/code/github/threefoldtech/0-robot
pip3 install -e .
cp utils/scripts/autobuild/startup.toml /.startup.toml
cp utils/scripts/autobuild/startup.py /.startup.py
popd

tar -cpzf "/tmp/archives/0-robot-autostart.tar.gz" --exclude tmp --exclude dev --exclude sys --exclude proc  /
