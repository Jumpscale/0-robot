#!/bin/bash
set -e

sudo chown $USER:$USER /opt/
sudo chown -R $USER:$USER /usr/local

# Install python3.5-dev
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.5-dev

# Instrall virtualenv
# sudo apt-get install -y python-virtualenv
# virtualenv -p python3.5 virtualenv
# . ./virtualenv/bin/activate

export ZUTILSBRANCH=zerorobot_fix
export JSBRANCH=${JSBRANCH:-master}

echo "INSTALL BASHTOOLS"
curl https://raw.githubusercontent.com/Jumpscale/bash/$ZUTILSBRANCH/install.sh?$RANDOM > /tmp/install.sh;bash /tmp/install.sh
 . /opt/code/github/jumpscale/bash/zlibs.sh

echo "install js9"
ZInstall_host_js9

pip3 install Cython
pip3 install asyncssh
pip3 install numpy
pip3 install tarantool
