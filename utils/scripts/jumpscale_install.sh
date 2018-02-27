#!/bin/bash
set -e

# settings
export BRANCH="merge_branches"

for target in /usr/local /opt /opt/cfg /opt/code/github/jumpscale /opt/var/capnp /opt/var/log $HOME/js9host/cfg; do
    mkdir -p $target
    sudo chown -R $USER:$USER $target
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


# create ssh key for jumpscale config manager
mkdir -p ~/.ssh
ssh-keygen -f ~/.ssh/id_rsa -P ''
eval `ssh-agent -s`
ssh-add ~/.ssh/id_rsa

# initialize jumpscale config manager
mkdir -p /opt/code/config_test
git init /opt/code/config_test
touch /opt/code/config_test/.jsconfig
js9_config init --silent --path /opt/code/config_test/ --key ~/.ssh/id_rsa