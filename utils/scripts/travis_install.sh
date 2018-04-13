#!/bin/bash
set -e

mkdir -p /opt/code/github/zero-os
sudo chown -R $USER:$USER /opt/code/github/zero-os
cp -r . /opt/code/github/zero-os/0-robot

pushd /opt/code/github/zero-os/0-robot
pip3 install .
popd


