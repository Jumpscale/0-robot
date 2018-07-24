from .filesystem import FileSystemServiceStorage


def get_storage(config):
    if config.data_repo.type == 'fs':
        return FileSystemServiceStorage(config.data_repo.path)
    raise RuntimeError("unsupported storage type for service %s", config.data_repo.type)
