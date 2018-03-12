from js9 import j
from zerorobot.errors import ExpectedError

SERVICE_STATE_OK = 'ok'
SERVICE_STATE_ERROR = 'error'
SERVICE_STATE_WARNING = 'warning'
SERVICE_STATE_SKIPPED = 'skipped'


class BadServiceStateError(Exception):
    """
    This exception is raised when trying to set a state to a value
    that is not supported
    """
    pass


class StateCategoryNotExistsError(Exception):
    """
    This exception is raised when trying to read the state of a
    category that doesn't exists
    """
    pass


class StateCheckError(ExpectedError, Exception):
    """
    This exception is raised when a call to ServiceState.check fails
    """
    pass

class ServiceState:
    """
    This class represent the state of the service.
    """

    def __init__(self):
        self.categories = {}

    def set(self, category, tag, state):
        """
        set a state to a value.
        """
        if state not in [SERVICE_STATE_OK, SERVICE_STATE_ERROR, SERVICE_STATE_WARNING, SERVICE_STATE_SKIPPED]:
            raise BadServiceStateError("state not supported: %s" % state)

        if category not in self.categories:
            self.categories[category] = {}

        self.categories[category][tag] = state

    def get(self, category, tag=None):
        """
        get the value of a state
        """
        if category not in self.categories:
            raise StateCategoryNotExistsError("category %s does not exists" % category)

        # we don't filer on tag, early return
        if tag is None:
            return self.categories[category]

        if tag not in self.categories[category]:
            raise StateCategoryNotExistsError("tag %s does not exists in category %s" % (tag, category))

        # return only the state for this tag
        # we return a dict so it's consistent with the case when tag is None
        return {tag: self.categories[category][tag]}

    def check(self, category, tag, expected):
        """
        checks if the state contains in category and tag is equal to expected
        if the category or the tag doesn't exists or the state is not equal to
        expected, raise StateCheckError, otherwise return True
        """
        err_msg = "check for state %s:%s:%s failed" % (category, tag, expected)
        try:
            state = self.get(category, tag)
            try:
                if not state[tag] == expected:
                    raise StateCheckError(err_msg)
            except KeyError:
                raise StateCheckError(err_msg)
        except StateCategoryNotExistsError:
            raise StateCheckError(err_msg)

        return True

    def delete(self, category, tag=None):
        """
        delete a state
        if tag is None, delete the full category
        """
        if category not in self.categories:
            return

        if tag is None:
            del self.categories[category]
            return

        if tag not in self.categories[category]:
            return

        del self.categories[category][tag]

    def save(self, path):
        """
        Serialize the state into a file

        @param path: file path where to save the state
        """
        j.data.serializer.yaml.dump(path, self.categories)

    def load(self, path):
        """
        Load the state from a file created by the save method

        @param path: file path from where to load the state
        """
        self.categories = j.data.serializer.yaml.load(path)

    def __repr__(self):
        return str(self.categories)

    __str__ = __repr__
