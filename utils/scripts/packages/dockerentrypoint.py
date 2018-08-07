#!/usr/bin/python3
import os
import time
import subprocess
from jumpscale import j

STANDARD_CONFIG_DIR = '/opt/code/local/stdorg/config'

if not j.sal.fs.exists("/root/.ssh/id_rsa"):
    j.tools.prefab.local.system.ssh.keygen(user='root', name='id_rsa')
    pubkey = j.sal.fs.readFile("/root/.ssh/id_rsa.pub")
    print("Configure the following ssh public key to have write access to your config / data repository:\n%s" % pubkey)
    exit(0)

config_repo = os.environ.get("config_repo")
if config_repo:
    path = j.tools.prefab.local.tools.git.pullRepo(config_repo)
else:
    j.sal.fs.createDir(STANDARD_CONFIG_DIR)
    path = STANDARD_CONFIG_DIR
    if not j.sal.fs.exists("%s/.git" % STANDARD_CONFIG_DIR):
        j.tools.prefab.local.core.run("cd %s && git init ." % STANDARD_CONFIG_DIR)

j.tools.prefab.local.core.run("js9_config init -s -k /root/.ssh/id_rsa -p %s" % path)

cmd_line = "zrobot server start"
args = [
    "listen",
    "data_repo",
    "template_repo",
    "config_repo",
    "debug",
    "telegram_bot_token",
    "telegram_chat_id",
    "auto_push",
    "auto_push_interval"
]
for arg in args:
    val = os.environ.get(arg, "").replace("'", "\\'")
    arg = arg.replace("_", "-")
    if val:
        if arg in ("debug", "auto-push"):
            cmd_line += " --%s" % arg
        elif arg == "template-repo":
            for val in val.split(','):
                cmd_line += " --%s '%s'" % (arg, val.strip())
        else:
            cmd_line += " --%s '%s'" % (arg, val.strip())

subprocess.run(cmd_line, shell=True)