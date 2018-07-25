import os
import shutil

from js9 import j

from .base import ServiceStorageBase, _serialize_service


class FileSystemServiceStorage(ServiceStorageBase):

    def __init__(self, path):
        super().__init__()
        self._root = path
        if not os.path.exists(path):
            os.makedirs(path)

    def _service_path(self, service):
        return os.path.join(
            self._root,
            service.template_uid.host,
            service.template_uid.account,
            service.template_uid.repo,
            service.template_uid.name,
            service.name,
            service.guid
        )

    def save(self, service):
        path = self._service_path(service)
        if not os.path.exists(path):
            os.makedirs(path)

        # location on the filesystem where to store the service
        serialized_service = _serialize_service(service)
        j.data.serializer.yaml.dump(os.path.join(path, 'service.yaml'), serialized_service['service'])
        j.data.serializer.yaml.dump(os.path.join(path, 'state.yaml'), serialized_service['states'])
        j.data.serializer.yaml.dump(os.path.join(path, 'data.yaml'), serialized_service['data'])
        j.data.serializer.yaml.dump(os.path.join(path, 'tasks.yaml'), serialized_service['tasks'])

    def list(self):
        for service_dir in j.sal.fs.listDirsInDir(self._root, recursive=True):
            info_path = os.path.join(service_dir, 'service.yaml')
            if not os.path.exists(info_path):
                continue

            info_data = j.data.serializer.yaml.load(info_path)
            state_data = j.data.serializer.yaml.load(os.path.join(service_dir, 'state.yaml'))
            data_data = j.data.serializer.yaml.load(os.path.join(service_dir, 'data.yaml'))
            tasks_data = j.data.serializer.yaml.load(os.path.join(service_dir, 'tasks.yaml'))

            yield {
                'service': info_data,
                'states': state_data,
                'data': data_data,
                'tasks': tasks_data,
            }

    def delete(self, service):
        path = self._service_path(service)
        if path and os.path.exists(path):
            shutil.rmtree(os.path.dirname(path))
