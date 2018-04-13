from urllib.parse import urlparse
import re

_version_regex = re.compile("(\d+).(\d+).(\d+)")
_name_regex = re.compile("^\w+$")


class TemplateUID:

    def __init__(self, host, account, repo, name, version):
        self.host = host
        self.account = account
        self.repo = repo
        self.name = name
        self.version = version

    @classmethod
    def parse(cls, uid):
        """
        Parse a template unique identifier.
        A tempate is identify by the url fo the git repository from where it comes from.
        There are different information extracted from
        - the host
        - the account
        - the repository name
        - the name of the template itself
        - a version
        e.g: github.com/account/repository/name/version would result into
        host: github.com
        account: account
        repository name: repository
        template name: name
        version: version

        parse supports forms:
        complete uid: github.com/account/repository/name/version
        without version: github.com/account/repository/name
        """
        host, account, repo, name, version = None, None, None, None, None

        parsed = urlparse(uid)
        if parsed.netloc:
            host = parsed.netloc

        ss = uid.rstrip('/').lstrip('/').split('/')

        if len(ss) == 5:
            host, account, repo, name, version = ss
        elif len(ss) == 4:
            host, account, repo, name = ss
        else:
            raise ValueError("format of the template uid (%s) not valid" % uid)

        if not _name_regex.match(name):
            raise ValueError("format of the template uid (%s) not valid" % uid)
        if version and not _version_regex.match(version):
            raise ValueError("format of the template uid (%s) not valid" % uid)

        return cls(host, account, repo, name, version)

    def tuple(self):
        l = [self.host, self.account, self.repo, self.name, self.version]
        return tuple(x for x in l if x)

    def __repr__(self):
        return '/'.join(self.tuple())

    def __str__(self):
        return repr(self)

    def __comp(self, other):
        if self.tuple()[:-1] != other.tuple()[:-1]:
            raise ValueError("other is not the same template, can't compare version")
        if self.version < other.version:
            return -1
        elif self.version > other.version:
            return 1
        else:
            return 0

    def __eq__(self, other):
        if isinstance(other, str):
            other = TemplateUID.parse(other)

        if not isinstance(other, TemplateUID):
            raise ValueError("other is not an instance of TemplateUID")

        return self.tuple() == other.tuple()

    def __lt__(self, other):
        return self.__comp(other) == -1

    def __le__(self, other):
        return self.__comp(other) in [0, -1]

    def __gt__(self, other):
        return self.__comp(other) == 1

    def __ge__(self, other):
        return self.__comp(other) in [0, 1]

    def __hash__(self):
        return hash(self.tuple())
