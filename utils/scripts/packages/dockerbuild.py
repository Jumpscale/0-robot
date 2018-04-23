#! /usr/bin/python3
"Docker image build script for 0-robot"
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
        "cd %s; pip install ." % path,
    )
    for cmd in cmds:
        prefab.core.run(cmd)


def build_docker(tag, jsbranch, zrbranch, push):
    "Build and push docker image for 0-robot"
    print("Starting docker container ... ", end='')
    j.sal.docker.client.images.pull(repository="ubuntu", tag="16.04")
    container = j.sal.docker.client.containers.create("ubuntu:16.04", command="sleep 3600")
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
        print("done!\nInstalling 0-robot ... ", end='')
        _install_zrobot(prefab, zrbranch)
        print("done!\nCommiting 0-robot docker image ... ", end='')
        container.commit("jumpscale/0-robot-tmp")
    finally:
        container.stop()
        container.remove()
    container = j.sal.docker.client.containers.create("jumpscale/0-robot-tmp",
                                                      command="/usr/bin/python3 /opt/code/github/jumpscale/0-robot/utils/scripts/packages/dockerentrypoint.py")
    container.commit("jumpscale/0-robot", tag)
    container.remove()
    if push:
        print("done!\nPushing docker image ... ")
        j.sal.docker.client.images.push("jumpscale/0-robot", tag)
        print("0-robot build and published successfully!")
    else:
        print("done!\n0-robot build successfully!")


def _main():
    import argparse
    parser = argparse.ArgumentParser("Build and push docker image for 0-robot")
    parser.add_argument("--tag", type=str, default="latest", help="Version tag for docker image")
    parser.add_argument("--jsbranch", type=str, default="development",
                        help="Jumpscale git branch, tag or revision to build")
    parser.add_argument("--zrbranch", type=str, default="master",
                        help="0-robot git branch, tag or revision to build")
    parser.add_argument("--push", help="Push to docker hub")
    parser.add_argument("--debug", help="Print debug information")
    args = parser.parse_args()
    if not args.debug:
        j.logger.set_mode(j.logger.PRODUCTION)
    build_docker(args.tag, args.jsbranch, args.zrbranch, args.push)


if __name__ == "__main__":
    _main()
