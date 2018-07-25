from .webhooks import Manager, FSStorage, ZDBStorage


def get(config):
    data_repo = config.data_repo
    if data_repo.type == 'fs':
        store = FSStorage(data_repo.path)
    elif data_repo.type == 'zdb':
        store = ZDBStorage(addr=data_repo.hostname,
                           port=data_repo.port,
                           admin_passwd=data_repo.username or '',
                           encr_key=data_repo.password or '')
    mgr = Manager(store)
    return mgr
