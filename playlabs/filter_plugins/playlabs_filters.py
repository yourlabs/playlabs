#!/usr/bin/python
import os


class FilterModule(object):
    def filters(self):
        return {
            'docker_env_dict': self.docker_env_dict,
            'exists': self.exists,
            'key_pub_exists': self.key_pub_exists,
            'key_pub_read': self.key_pub_read,
        }

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
