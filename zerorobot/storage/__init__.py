from .filesystem import FileSystemServiceStorage
from .zdb import ZDBServiceStorage


def get(config):
    data_repo = config.data_repo
    if data_repo.type == 'fs':
        return FileSystemServiceStorage(data_repo.path)
    if data_repo.type == 'zdb':
        return ZDBServiceStorage(addr=data_repo.hostname,
                                 port=data_repo.port,
                                 admin_passwd=data_repo.username,
                                 encr_key=data_repo.password)

    raise RuntimeError("unsupported storage type for service %s", data_repo.type)
