#!/bin/bash
set -e

cd /opt
git clone https://github.com/Jumpscale/sandbox_linux
git clone https://github.com/zero-os/0-robot

cd sandbox_linux/sandbox
source env.sh
cd ../../0-robot
pip3 install .

cd /tmp/target
tar -czf /tmp/archives/dnsmasq.tar.gz *
