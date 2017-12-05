#!/bin/bash
set -e

# Install python3.5
# sudo add-apt-repository -y ppa:deadsnakes/ppa
# sudo apt-get update
# sudo apt-get install -y python3.5

# Instrall virtualenv
# sudo apt-get install -y python-virtualenv
# virtualenv -p python3.5 virtualenv
# . ./virtualenv/bin/activate

# Install python3.5-dev
sudo apt-get install -y python3.5-dev

export ZUTILSBRANCH=${ZUTILSBRANCH:-master}
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
