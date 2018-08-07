from jumpscale import j

def _container_create(name, base=None, start=True, ssh=False):
    if base:
        container = j.sal.docker.create(name, ssh=ssh, base=base)
    else:
        container = j.sal.docker.create(name, ssh=ssh)
    if start:
        container.start()
    return container

def _install_js(prefab, branch):
    # prefab.core.run("sed -i 's/filter = \\[\\]/filter = [\"*\"]/g' /root/js9host/cfg/jumpscale9.toml")
    prefab.js9.js9core.install(branch=branch, full=True)

def _install_zrobot(prefab, branch):
    prefab.system.package.install('libcapnp-dev') #capnp dependency
    path = prefab.tools.git.pullRepo("https://github.com/Jumpscale/0-robot.git")
    cmds = (
        "cd %s; git checkout %s" % (path, branch),
        "cd %s; pip install -r requirements.txt" % path,
        "cd %s; pip install ." % path, # uncomment after solving 0-robot installation issue
    )
    prefab.runtimes.pip.ensure()
    for cmd in cmds:
        prefab.core.run(cmd)


def build_container_zrobot(name, jsbranch, zrbranch, push=True):
    "Build and push docker image for 0-robot"
    print("Starting docker container ... ", end='')
    container = _container_create(name)
    ex = j.tools.executor.getLocalDocker(container.id)
    try:
        prefab = ex.prefab
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
        container.destroy()
    container = j.sal.docker.create("jumpscale-0-robot-tmp",
                command="/usr/bin/python3 /opt/code/github/jumpscale/0-robot/utils/scripts/packages/dockerentrypoint.py")
    container.commit("jumpscale/0-robot")
    container.destroy()
    if push:
        print("done!\nPushing docker image ... ")
        j.sal.docker.client.push("jumpscale/0-robot")
        print("0-robot build and published successfully!")
    else:
        print("done!\n0-robot build successfully!")

def build_container_jumpscale(name, jsbranch, push=True):
    "Build and push docker image for JumpScale"
    print("Starting docker container ... ", end='')
    container = _container_create(name, ssh=False)
    ex = j.tools.executor.getLocalDocker(container.id)
    try:
        ex.state_disabled = True
        prefab = ex.prefab
        print("done!\nUpdating ubuntu apt definitions ... ", end='')
        prefab.system.package.mdupdate()
        print("done!\nInstalling python3-dev, git, curl & language-pack-en ... ", end='')
        prefab.system.package.install("python3-dev,git,curl,language-pack-en")
        print("done!\nInstalling jumpscale ... ", end='')
        _install_js(prefab, jsbranch)
        print("done!\nCommiting JumpScale docker image ... ", end='')
        container.commit("jumpscale/js9-full")
    except Exception as e:
        print(e)
        print('JumpScale installation failed, will delete created docker')
        container.stop()
        container.destroy()
        return
    if push:
        print("done!\nPushing docker image ... ")
        j.sal.docker.client.push("jumpscale/js9-full")
        print("JumpScale build and published successfully!")
    else:
        print("done!\nJumpScale build successfully!")

from IPython import embed
embed()
# build_container_jumpscale('js9_full','development')