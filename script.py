import os
import requests
from requests.auth import HTTPBasicAuth
#from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth1Session
import logging
import re
from mixins.fs import FsMixin

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
        headers = ['status', 'x-ratelimit-limit', 'x-ratelimit-remaining']
        for header in headers:
            if header in r.headers.keys():
                log.info('%s: %s' % (header, r.headers[header]))
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

class Backup(FsMixin):
    def __init__(self):
        self._c = Connection()
        self._base_work = "./work"

        self._c.get("/user")
        self._makedirs(self._base_work)


    def _bare(self, repo):
        pass

    def _branch(self, repo, branch="master"):
        pass

    def _zip(self, repo):
        pass

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
        self._rmtree(self._base_work)

    def run(self):
        i = 0
        for repo in self.repos:
            if i == 2:
                break
            print(" o %s: fork(%s) starred(%s), private? %s :: (%s)" % (repo["full_name"], repo["forks"], repo["stargazers_count"], repo["private"], repo["git_url"]))
            repo["local_uri"] = "./work/%s"
            self._bare(repo)
            self._zip()
            i += 1
        self._clean()

if __name__ == "__main__":
    try:
        b = Backup()
        b.run() #filter=["skies-io/*"]
    except Exception as e:
        print(e)
