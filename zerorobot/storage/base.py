
from abc import ABC, abstractmethod


class ServiceStorageBase(ABC):

    @abstractmethod
    def save(self, service):
        """
        save a service object

        :param service: service
        :type service: zerorobot.template.base
        """

    @abstractmethod
    def list(self):
        """
        yield all the services data found in the storage

        this method yield a dict containing all the data of a service
        example of such a dict:
        {
            'service':{
                'template': '',
                'version': '',
                'name': '',
                'guid': '',
                'public': '',
            },
            'states':{
                'category1':{
                    'name': 'state',
                },
                'category2':{
                    'name': 'state',
                }
            },
            'data': {
                ...
            },
            'tasks': [
                {
                    "guid":: '',
                    "action_name": '',
                    "args": '',
                    "state": '',
                    "eco": '',
                    "created": '',
                }
            ]
        }
        """

    @abstractmethod
    def delete(self, service):
        """
        delete a service

        :param service: service
        :type service: zerorobot.template.base
        """



def _serialize_service(service):
    return {
        'service': _serialize_service_info(service),
        'states': service.state.categories,
        'data': dict(service.data),
        'tasks': [_serialize_task(task) for task in service.task_list.list_tasks(all=False)]
    }


def _serialize_service_info(service):
    return {
        'template': str(service.template_uid),
        'version': service.version,
        'name': service.name,
        'guid': service.guid,
        'public': service._public,
    }


def _serialize_task(task):
    return {
        "guid": task.guid,
        "action_name": task.action_name,
        "args": task._args,
        "state": task.state,
        "eco": task.eco.to_dict() if task.eco else None,
        "created": task.created,
    }
