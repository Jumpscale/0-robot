#!/bin/bash
set -x

export SSHKEYNAME=id_rsa

# Start js9 container
sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; ZDockerActive -b jumpscale/js9_full -i js9_full"

# Install pytest
sudo -HE bash -c "ssh -tA  root@localhost -p 2222 \"pip install -U pycodestyle nose2\""

# Run tests
sudo -HE bash -c "ssh -tA  root@localhost -p 2222 \"cd /opt/code/github/jumpscale/zerorobot; pycodestyle --show-source --show-pep8 --ignore=E501 zerorobot\""
sudo -HE bash -c "ssh -tA  root@localhost -p 2222 \"cd /opt/code/github/jumpscale/zerorobot; nose2\""
