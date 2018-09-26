#!/usr/bin/python

class FilterModule(object):
    def filters(self):
        return {
            'docker_env_dict': self.docker_env_dict,
        }

    def docker_env_dict(self, env):
        return {
            i.split('=')[0]: i.split('=')[1]
            for i in env
        }
