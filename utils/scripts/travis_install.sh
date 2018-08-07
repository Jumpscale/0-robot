#!/bin/bash
set -e

mkdir -p /opt/code/github/threefoldtech
sudo chown -R $USER:$USER /opt/code/github/threefoldtech
cp -r . /opt/code/github/threefoldtech/0-robot

pushd /opt/code/github/threefoldtech/0-robot
pip3 install .
popd


