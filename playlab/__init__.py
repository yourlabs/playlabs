"""
playlab is a command to wrap around ansible.
"""
import copy
from functools import partialmethod
import json
import os
import shlex
import subprocess

from clitoo import context

from processcontroller import ProcessController

os.environ.setdefault('ANSIBLE_STDOUT_CALLBACK', 'yaml')


class Host:
    def __init__(self, arg):
        self.user = os.getenv('USER')
        self.password = None

        if '@' not in arg:
            self.host = arg
        else:
            left, self.host = arg.split('@')
            self.user, self.password = left.split(':')


class Inventory:
    def __init__(self):
        self.file = context.take('i', 'file')
        if not self.file:
            self.file = self.find()
        self.dir = os.path.dirname(self.file)

    def find(self):
        paths = [
            'inventory.yaml',
            'inventory.yml',
            'inventory/inventory.yaml',
            'inventory/inventory.yml',
        ]

        for path in path:
            if os.path.exists(path):
                return path


class Key:
    def __init__(self, play):
        self.play = play

    def get_ssh_key(self):
        if self.play.inventory.dir and self.parser.user:
            inv_key = os.path.join(
                self.INVENTORY_DIR,
                'keys',
                self.parser.user
            )

            if os.path.exists(inv_key):
                print(f'Using {inv_key}')

                with open(inv_key, 'r') as f:
                    content = f.read()

                if 'ANSIBLE_VAULT' in content:
                    decrypted_vault = self.vault.decrypt(inv_key)
                    self.set_ssh_key(decrypted_vault)
                else:
                    self.set_ssh_key(inv_key)

                return

        key = os.getenv('SSH_PRIVATE_KEY')
        if key:
            print('Using SSH_PRIVATE_KEY env var')
            self.set_ssh_key(key)

    def set_ssh_key(self, key):
        with open(self.key_path, 'wb+') as f:
            if isinstance(key, str):
                print('Encoding string key to bytes with unicode')
                key = key.encode('utf8')
            f.write(key)
        os.chmod(self.key_path, 0o700)

    def unset_ssh_key(self):
        if os.path.exists(self.key_path):
            os.unlink(self.key_path)


class Options:
    def __init__(self):
        self.sudo = not context.take('nosudo')

        if 'i' not in context.args and 'inventories' not in context.args:
            default_inventory = os.path.join(
                os.getcwd(), 'inventory.yml')
            if not os.path.exists(default_inventory):
                default_inventory = None

        self.inventories = context.take('i', 'inventory', default=default_inventory)

        self.args = []

    def ansible_options(self):
        if '--become' not in options:
            args.append('--become')
        if '--become-method' not in options:
            args += ['--become-method', 'sudo']
        if '--become-user' not in options:
            args += ['--become-user', 'root']


class Play:
    def __init__(self, hosts, variables):
        self.hosts = hosts
        self.variables = variables

    def playbook(self, name, variables=None):
        variables = variables or dict()
        variables.update(self.variables)

        cmd = [
            subprocess.check_output(
                ('/bin/which', 'ansible-playbook')
            ).decode('utf8').strip()
        ]
        cmd.append('-v')

        cmd += ['-e', json.dumps(variables)]

        password = None
        for host in self.hosts:
            if host.password:
                password = host.password

        cmd.append(name)
        print([shlex.quote(i) for i in cmd])
        print(' '.join(cmd))

        pc = ProcessController()
        pc.run(
            cmd,
            dict(
                when=[
                    [
                        '^SSH password.*',
                        partialmethod(
                            pc.send,
                            str(password),
                        )
                    ],
                    [
                        '^BECOME password.*',
                        partialmethod(
                            pc.send,
                            str(password),
                        )
                    ],
                ]
            )
        )
        pc.close()
        return pc.wait()

        '''
        cmd += self.inventory()
        cmd += args
        if os.path.exists(self.key_path):
            cmd += ['--private-key', self.key_path]
        cmd.append(os.path.join(self.PLAYBOOKS, name))
        '''


def role(roles, *args, **variables):
    playbook = os.path.join(
        os.path.dirname(__file__),
        'role.yml',
    )

    hosts = []
    for arg in args:
        if arg.startswith('{'):
            variables.update(json.loads(arg))
        else:
            hosts.append(Host(arg))

    play = Play(hosts, variables)
    import ipdb; ipdb.set_trace()

    for role in roles.split(','):
        play = play.playbook(
            os.path.join(
                os.path.dirname(__file__),
                'role.yml',
            ),
            variables=dict(
                role=role,
            )
        )


def play(playbook, *args, **kwargs):
    """
    """
    import ipdb; ipdb.set_trace()
