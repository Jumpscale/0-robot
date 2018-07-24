class ServiceStorageBase:

    def save(self, service):
        """
        save a service object

        :param service: service
        :type service: zerorobot.template.base
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def delete(self, service):
        raise NotImplementedError()
