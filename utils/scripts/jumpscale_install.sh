#!/bin/bash
set -e

# settings

export CORE_REVISION="development"
export LIB_REVISION="development"
export PREFAB_REVISION="development"

for target in /usr/local /opt /opt/cfg /opt/code/github/threefoldtech /opt/var/capnp /opt/var/log $HOME/jumpscale/cfg; do
    mkdir -p $target
    sudo chown -R $USER:$USER $target
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
    pip3 install .
    popd
done
popd


# create ssh key for jumpscale config manager
mkdir -p ~/.ssh
ssh-keygen -f ~/.ssh/id_rsa -P ''
eval `ssh-agent -s`
ssh-add ~/.ssh/id_rsa

# initialize jumpscale config manager
mkdir -p /opt/code/config_test
git init /opt/code/config_test
touch /opt/code/config_test/.jsconfig
js_config init --silent --path /opt/code/config_test/ --key ~/.ssh/id_rsa