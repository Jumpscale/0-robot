#!/usr/bin/python3
import os
import time
from js9 import j

if os.environ.get("dockerbuild"):
    exit(0)

if not j.sal.fs.exists("/root/.ssh/id_rsa"):
    j.tools.prefab.local.system.ssh.keygen(user='root', name='id_rsa')
    j.tools.prefab.local.core.run("js9_config init -s")

cmd_line = "zrobot server start"
args = [
    "listen", 
    "data-repo", 
    "template-repo", 
    "config-repo", 
    "debug", 
    "telegram-bot-token", 
    "telegram-chat-id", 
    "auto-push", 
    "auto-push-interval"
]
for arg in args:
    val = os.environ.get("val")
    if val:
        if arg in ("debug", "auto-push"):
            cmd_line += " --%s" % arg
        else:
            cmd_line += " --%s '%s'" % (arg, val.replace("'", "\\'"))

j.tools.prefab.local.core.run(cmd_line)