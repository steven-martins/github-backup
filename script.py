import os
import requests
from requests.auth import HTTPBasicAuth
#from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth1Session
import logging
import re
from mixins.fs import FsMixin
from mixins.scm import GitMixin

class ResponseException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_logger(name, level=None):
    logger = logging.getLogger(name)
    if not logger.handlers:
        stderr = logging.StreamHandler()
        stderr.setFormatter(logging.Formatter(
            '%(levelname)s [%(name)s]: %(message)s'))
        logger.addHandler(stderr)
        level = level if level else os.environ.get('GITHUB_LOGLEVEL', 'CRITICAL')
        logger.setLevel(getattr(logging, level))
    return logger


log = get_logger('response')

class Response(object):
    def __init__(self, data, links={}):
        self.data = data
        self.links = links


class Connection(object):
    def __init__(self):
        self.base = 'https://api.github.com'
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(os.getenv("GITHUB_LOGIN"), os.getenv("GITHUB_PAT"))

    def _links(self, hdr):
        links = {}
        for s in hdr.split(','):
            link = {}
            m = re.match('<(.*)\?(.*)>', s.split(';')[0].strip())
            link["uri"] = m.groups()[0]
            link["params"] = {}
            for kv in m.groups()[1].split('&'):
                key, value = kv.split('=')
                link["params"][key] = value
            m = re.match('rel="(.*)"', s.split(';')[1].strip())
            rel = m.groups()[0]
            links[rel] = link
            log.debug('link-%s-page: %s' % (rel, link["params"]['page']))
        return links

    def get(self, url, params={}):
        r = self.session.get(self.base + url, params=params)
        if not r.status_code in (200, 201, 204):
            raise ResponseException(r.text)
        links = {}
        if 'link' in r.headers.keys():
            links = self._links(r.headers['link'])
        return Response(r.json(), links)


class Pager(object):
    def __init__(self, conn, uri, params={}):
        self.conn = conn
        self.uri = uri
        self.params = params

    def __iter__(self):
        while True:
            response = self.conn.get(self.uri, self.params)
            yield response
            if not 'next' in response.links.keys():
                break
            m = re.match(self.conn.base + '(.*)', response.links["next"]["uri"])
            self.uri = m.groups()[0]
            self.params = response.links["next"]["params"]


class Backup(GitMixin):
    def __init__(self):
        self._c = Connection()
        self._base_work = "/tmp/work"
        self._base_archives = "./archives/"

        self._c.get("/user")
        self._makedirs(self._base_work)
        self._makedirs(self._base_archives)

    def _bare(self, repo):
        name = self._cleanfilename(repo["full_name"])
        local_path = os.path.join(self._base_work, name)
        self._makedirs(local_path)
        status, obj = self._retrieve_bare_(local_path, repo["ssh_url"])
        return obj

    def _clone(self, repo):
        name = self._cleanfilename(repo["full_name"])
        local_path = os.path.join(self._base_work, name)
        #self._makedirs(local_path)
        status, obj = self._retrieve_repository_(local_path, repo["ssh_url"])
        return obj

    def _arch(self, repo, local_repo, branch="master"):
        name = "%s-%s" % (self._cleanfilename(repo["full_name"]), branch)
        local_path = os.path.join(os.path.abspath(self._base_work), self._cleanfilename(repo["full_name"]))
        dest = os.path.join(os.path.abspath(self._base_archives), self._cleanfilename(repo["full_name"]))
        self._makedirs(dest)
        archive_name = "%s.zip" % os.path.join(dest, name)
        return local_repo.archive(branch, archive_name)

    def _zip(self, repo, t="bare"):
        name = "%s-%s" % (self._cleanfilename(repo["full_name"]), t)
        local_path = os.path.join(os.path.abspath(self._base_work), self._cleanfilename(repo["full_name"]))
        archive_name = self._archive(self._base_archives, name, local_path)

    @property
    def repos(self):
        p = Pager(self._c, "/user/repos")
        for page in p:
            repos = page.data
            for repo in repos:
                yield repo

    def backup(self, repo):
        pass

    def _clean(self):
        self._rmtree(self._base_work, safe=True)

    def run(self):
        for repo in self.repos:
            print(" o %s: fork(%s) starred(%s), private? %s, size(%s) :: (%s)" % (repo["full_name"], repo["forks"], repo["stargazers_count"], repo["private"], repo["size"], repo["ssh_url"]))
            repo["local_uri"] = "./work/%s"
            obj = self._bare(repo)
            self._zip(repo)
            obj.remove()
            obj = self._clone(repo)
            for branch in obj.branches():
                print("   -> %s" % branch)
                self._arch(repo, obj, branch)
            obj.remove()
        self._clean()

if __name__ == "__main__":
    try:
        b = Backup()
        b.run() #filter=["skies-io/*"]
    except Exception as e:
        print(e)
