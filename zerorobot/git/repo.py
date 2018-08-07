from jumpscale import j


class Repo:

    def __init__(self, path):
        self.repo = j.clients.git.get(path)

    @classmethod
    def clone(cls, url, branch='master'):
        path = j.clients.git.pullGitRepo(url, branch=branch)
        return cls(path)

    def branch_or_tag(self):
        return self.repo.getBranchOrTag()

    def pull(self):
        self.repo.pull()

    def fetch(self):
        self.repo.fetch()

    def switch_branch(self, branch):
        self.repo.switchBranch(branch, create=False)

    def switch_tag(self, tag):
        self.repo.checkout(tag)


class RepoCheckoutError(Exception):
    """
    Exception raised when the checkout of a branch/tag/revision failed on a repo
    """

    def __init__(self, msg, original_exception):
        super().__init__(msg + (": %s" % original_exception))
        self.original_exception = original_exception
