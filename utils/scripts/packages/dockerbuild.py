#! /usr/bin/python3
"Docker image build script for 0-robot"
import docker
import json

from js9 import j


REPOSITORY = "jumpscale/0-robot"


def _install_js(prefab, branch):
    prefab.js9.js9core.install(branch=branch)
    for component in ("core9", "lib9", "prefab9"):
        cmd = "cd /opt/code/github/jumpscale/%s; pip install ." % component
        prefab.core.run(cmd)
    prefab.executor.execute("sed -i 's/filter = \\[\\]/filter = [\"*\"]/g' /root/js9host/cfg/jumpscale9.toml")


def _install_zrobot(prefab, branch):
    path = prefab.tools.git.pullRepo("https://github.com/Jumpscale/0-robot.git")
    cmds = (
        "cd %s; git checkout %s" % (path, branch),
        "cd %s; pip install -r requirements.txt" % path,
        "cd %s; pip install ." % path,
    )
    for cmd in cmds:
        prefab.core.run(cmd)


def _add_startup(prefab):
    content = """
[startup.zrobot]
name = "core.system"
protected = true #set protected to true to respawn the container if it crashed
running_delay = -1

[startup.zrobot.args]
name = "/usr/local/bin/zrobot"
args = ["server", "start", "-T", "http://github.com/zero-os/0-templates"]
"""
    prefab.executor.file_write("/.startup.toml", content)


def build_docker(tag, jsbranch, zrbranch, push):
    """
    Build and push docker image for 0-robot
    :param tag: image tag
    :param jsbranch: jumpscale branch
    :param zrbranch: zero robot branch
    :param push: boolen indicating whether the image should be pushed or not
    """
    print("Starting docker container ... ", end='')
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    client.images.pull(repository="ubuntu", tag="16.04")
    container = client.containers.create("ubuntu:16.04", command="sleep 3600")
    container.start()
    print("done!\nEstablishing prefab connection ... ", end='')

    try:
        ex = j.tools.executor.getLocalDocker(container.id)
        prefab = j.tools.prefab.get(executor=ex)
        print("done!\nUpdating ubuntu apt definitions ... ", end='')
        prefab.system.package.mdupdate()
        print("done!\nInstalling python3-dev, git, curl & language-pack-en ... ", end='')
        prefab.system.package.install("python3-dev,git,curl,language-pack-en")
        print("done!\nInstalling jumpscale ... ", end='')
        _install_js(prefab, jsbranch)
        print("done!\n Adding startup script.....")
        _add_startup(prefab)
        print("done!\nInstalling 0-robot ... ", end='')
        _install_zrobot(prefab, zrbranch)
        print("done!\nCommiting 0-robot docker image ... ", end='')
        container.commit("jumpscale/0-robot-tmp")
    finally:
        container.stop()
        container.remove()
    container = client.containers.create(
        "jumpscale/0-robot-tmp",
        command="/usr/bin/python3 /opt/code/github/jumpscale/0-robot/utils/scripts/packages/dockerentrypoint.py")
    container.commit("jumpscale/0-robot", tag)
    container.remove()

    if push:
        print("done!\nPushing docker image ... ", end="")
        client.images.push("jumpscale/0-robot", tag)
        print("0-robot build and published successfully!", end="")
    else:
        print("done!\n0-robot build successfully!")


def convert_docker(iyo):
    """
    Convert docker image to flist on hub.gig.tech
    :param iyo: iyo client instance name
    """
    print("Starting convert docker to flist......")
    iyo_client = j.clients.itsyouonline.get(iyo)
    jwt = iyo_client.jwt_get()
    _, res, _ = j.tools.prefab.local.executor.execute(
        "curl -b 'caddyoauth=%s' -d image=jumpscale/0-robot https://hub.gig.tech/api/flist/me/docker" % jwt)

    response = json.loads(res)
    if response["status"] == "success":
        print("done!\.....0-robot docker converted to flist successfully!")
    else:
        print("error!....something went wrong....received status %s" % response["status"])


def _main():
    import argparse
    parser = argparse.ArgumentParser("Build and push docker image for 0-robot")
    parser.add_argument("--tag", type=str, default="latest", help="Version tag for docker image")
    parser.add_argument("--jsbranch", type=str, default="development",
                        help="Jumpscale git branch, tag or revision to build")
    parser.add_argument("--zrbranch", type=str, default="master",
                        help="0-robot git branch, tag or revision to build")
    parser.add_argument("--push", const=True, nargs='?', type=bool, help="Push to docker hub")
    parser.add_argument("--flist", const=True, nargs='?', type=bool, help="Convert to flist on hub.gig.tech")
    parser.add_argument("--iyo", type=str, default="main", help="iyo instance name")
    parser.add_argument("--debug", const=True, nargs='?', type=bool, help="Print debug information")

    args = parser.parse_args()
    if args.debug:
        j.logger.loggers_level_set(level='DEBUG')

    if args.flist and not args.push:
        raise ValueError("flist can't be true if push is false")

    build_docker(args.tag, args.jsbranch, args.zrbranch, args.push)

    if args.flist:
        convert_docker(args.iyo)

if __name__ == "__main__":
    _main()
