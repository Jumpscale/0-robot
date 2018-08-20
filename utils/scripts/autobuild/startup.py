import shlex
import os
from jose import jwt

from jumpscale import j

iyo_pub_key = """-----BEGIN PUBLIC KEY-----
MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAES5X8XrfKdx9gYayFITc89wad4usrk0n2
7MjiGYvqalizeSWTHEpnd7oea9IQ8T5oJjMVH5cc0H5tFSKilFFeh//wngxIyny6
6+Vq5t5B0V0Ehy01+2ceEon2Y0XDkIKv
-----END PUBLIC KEY-----"""


def configure_local_client():
    j.sal.fs.createDir('/opt/code/local/stdorg/config/j.clients.zos_protocol')
    j.sal.fs.writeFile('/opt/code/local/stdorg/config/j.clients.zos_protocol/local.toml', """
    db = 0
    host = '127.0.0.1'
    password_ = ''
    port = 6379
    ssl = true
    timeout = 120
    unixsocket = '/tmp/redis.sock'
    """)


def get_admin_organization(kernel_args):
    """
    decide which organization to use to protect admin endpoint of the 0-robot API

    first we check if there is a farmer_id token
    if it exists, we extract the organization from it and use it
    if it doesn't we check if there is an organization kernel parameter and use it
    if still don't have an organization, we return None
    """

    org = None
    token = kernel_args.get('farmer_id')
    if token:
        try:
            claims = jwt.decode(token, iyo_pub_key)
        except jwt.ExpiredSignatureError:
            token = j.clients.itsyouonline.refresh_jwt_token(token)
            claims = jwt.decode(token, iyo_pub_key)
        for scope in claims.get('scope'):
            if scope.find('user:memberof:') != -1:
                org = scope[len('user:memberof:'):]
                break
    else:
        org = kernel_args.get('admin_organization')
        if not org:
            org = kernel_args.get('organization')

    return org


def get_user_organization(kernel_args):
    return kernel_args.get('user_organization')


def read_kernel():
    """
    read the kernel parameter passed to the host machine
    return a dict container the key/value of the arguments
    """
    with open('/proc/cmdline') as f:
        line = f.read()

    args = {}
    line = line.strip()
    for kv in shlex.split(line):
        ss = kv.split('=', 1)
        if len(ss) == 2:
            args[ss[0]] = ss[1]
        elif len(ss) <= 1:
            args[ss[0]] = None
    return args


def start_robot():
    kernel_args = read_kernel()
    args = ['zrobot', 'server', 'start', '--mode', 'node']

    # don't forget to remove #development when merging into master
    template_repo = 'https://github.com/threefoldtech/0-templates#development'

    admin_org = get_admin_organization(kernel_args)
    if admin_org:
        args.extend(['--admin-organization', admin_org])

    user_org = get_user_organization(kernel_args)
    if user_org:
        args.extend(['--user-organization', user_org])

    if 'development' in kernel_args:
        args.append('--god')

    args.extend(['--template-repo', template_repo])

    print('starting node robot: %s' ' '.join(args))

    os.execv('usr/local/bin/zrobot', args)


def main():
    configure_local_client()
    start_robot()


if __name__ == '__main__':
    main()
