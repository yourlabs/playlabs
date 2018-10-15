#!/usr/bin/python
from urllib.parse import urlparse
import os
import subprocess

from ansible import errors


class FilterModule(object):
    def filters(self):
        return {
            'docker_env_dict': self.docker_env_dict,
            'exists': self.exists,
            'key_pub_exists': self.key_pub_exists,
            'key_pub_read': self.key_pub_read,
            'vaulted_password': self.vaulted_password,
            'vaulted_read': self.vaulted_read,
            'url_only': self.url_only,
        }

    def url_only(self, url):
        o = urlparse(url)
        return f'{o.scheme}://{o.netloc}'

    def key_pub_exists(self, name):
        return os.path.exists(f'keys/{name}.pub')

    def key_pub_read(self, name):
        with open(f'keys/{name}.pub', 'r') as f:
            return f.read()

    def exists(self, path):
        return os.path.exists(path)

    def docker_env_dict(self, env):
        return {
            i.split('=')[0]: i.split('=')[1]
            for i in env
        }

    def vaulted_read(self, path, default=None):
        if not os.path.exists(path):
            if default is not None:
                return default
            raise errors.AnsibleFilterError(
                f'{path} not found and no default provided')
        out = subprocess.check_output([
            'ansible-vault',
            'view',
            path,
        ])
        return out.decode('utf8').strip()

    def vaulted_password(self, name, default=None):
        path = os.path.join('passwords/', name)
        return self.vaulted_read(path, default)
