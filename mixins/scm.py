__author__ = 'steven'

from .fs import FsMixin
from .execution import ExecMixin
from exceptions import NotImplemented
import logging
import config
import os
import time


class GitRepository(FsMixin):
    def __init__(self, local_uri, uri):
        self._local_uri = local_uri
        self._uri = uri
        self._messages = ""
        self._status = None
        self._date = None

    def clone(self, bare=False):
        logging.debug("GitRepository::clone uri(%s), local_uri(%s)" % (self._uri, self._local_uri))
        if os.path.exists(self._local_uri) and os.listdir(self._local_uri):
            logging.warning("GitRepository::clone local_uri(%s) not empty" % (self._local_uri))
            self._rmtree(self._local_uri, True)
            #return False
        self._date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        if bare:
            res = self._safe_exec(["git", "clone", "--bare", self._uri, self._local_uri], timeout=config.GIT_CLONE_TIMEOUT)
        else:
            res = self._safe_exec(["git", "clone", "--depth", str(config.GIT_MAX_DEPTH), self._uri, self._local_uri], timeout=config.GIT_CLONE_TIMEOUT)
        if res.return_code == 0:
            self._status = "Success"
            self._messages += "OK. "
            return True
        self._messages += "%s. " % (str(res.exception) if res.exception else res.errs.decode("utf-8"))
        self._status = "Fail"
        return False

    def clone_with_retries(self, count=3, bare=False):
        for i in range(count):
            self.remove()
            self._messages += "[%s/%s] " % (i, count)
            if self.clone():
                return True
            time.sleep(0.2)
        return False

    def exists(self):
        return os.path.exists(os.path.join(self._local_uri, ".git"))

    def branches(self):
        branches = []
        print(self._local_uri)
        res = self._safe_exec(["git", "branch", "-r", "--list", "--no-color"], cwd=self._local_uri, timeout=config.GIT_CLONE_TIMEOUT)

        if res.return_code == 0:
            for line in res.outs.decode("utf-8").split("\n"):
                if "/" in line and "->" not in line:
                    branches.append(line.split("/")[1])
        return branches

    def succeed(self):
        return self._status == "Success"

    def pull(self):
        raise NotImplemented()

    def archive(self, branch, filename):
        res = self._safe_exec(["git", "archive", "--format=zip", "-o", filename, "origin/%s" % branch], cwd=self._local_uri, timeout=config.GIT_CLONE_TIMEOUT)
        return res.return_code == 0

    def checkout(self, branch):
        res = self._safe_exec(["git", "checkout", branch], cwd=self._local_uri, timeout=config.GIT_CLONE_TIMEOUT)
        return res.return_code == 0

    def clean(self):
        self._rmtree(os.path.join(self._local_uri, ".git"), safe=True)

    def remove(self):
        if os.path.exists(self._local_uri):
            self._rmtree(self._local_uri, safe=True)

class GitMixin(FsMixin):
    def __init__(self):
        pass

    def _retrieve_bare_(self, local_uri, uri):
        obj = GitRepository(local_uri, uri)
        obj.clone(bare=True)
        return obj.succeed(), obj

    def _retrieve_repository_(self, local_uri, uri):
        obj = GitRepository(local_uri, uri)
        obj.clone()
        #obj.clean()
        return obj.succeed(), obj

    def _remove_repository_(self, local_uri):
        obj = GitRepository(local_uri, "")
        return obj.remove()
