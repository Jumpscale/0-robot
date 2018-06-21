from js9 import j

FLIST_HASH = '679d829a0d'
VERSION = '0.7.2'


iyo = j.clients.itsyouonline.get()
jwt = iyo.jwt_get(scope='user:memberof:gig-official-apps')
data = {
    'token_': jwt,
    'username': 'gig-official-apps',
    'url': 'https://hub.gig.tech/api',
}

j.clients.zerohub.delete('official-apps')
hub = j.clients.zerohub.get('official-apps', data=data, interactive=False)
hub.authenticate()
hub.api.set_user('gig-official-apps')


hub.promote('gig-autobuilder', 'zero-os-0-robot-master-%s.flist' % FLIST_HASH, 'zero-os-0-robot-%s.flist' % VERSION)
hub.promote('gig-autobuilder', 'zero-os-0-robot-autostart-master-%s.flist' % FLIST_HASH, 'zero-os-0-robot-autostart-%s.flist' % VERSION)

hub.symlink('zero-os-0-robot-%s.flist' % VERSION, 'zero-os-0-robot-latest.flist')
hub.symlink('zero-os-0-robot-autostart-%s.flist' % VERSION, 'zero-os-0-robot-autostart-latest.flist')
