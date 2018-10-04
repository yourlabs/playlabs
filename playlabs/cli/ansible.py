import os
import shlex
import subprocess
import sys

import sh

import yaml

import pexpect

from .tools import known_host


PLAYBOOKS = os.path.join(os.path.dirname(__file__), os.pardir)
INVENTORY_FILE = None
INVENTORY_DIR = None
find = [
    'inventory.yaml',
    'inventory.yml',
    'inventory/inventory.yaml',
    'inventory/inventory.yml',
]
for i in find:
    print(f'Looking for inventory file {i}')
    if os.path.exists(i):
        INVENTORY_FILE = i
        break

if INVENTORY_FILE:
    INVENTORY_DIR = os.path.dirname(INVENTORY_FILE)


class Ansible(object):
    def __init__(self, parser):
        os.environ.setdefault('ANSIBLE_STDOUT_CALLBACK', 'yaml')
        self.parser = parser
        self.vault = Vault()

    def sudo(self, options):
        if '--become' not in options:
            options.append('--become')
        if '--become-method' not in options:
            options += [
                '--become-method', 'sudo',
            ]
        if '--become-user' not in options:
            options += [
                '--become-user', 'root'
            ]
        return options

    def inventory(self):
        if INVENTORY_FILE:
            return ['--inventory', INVENTORY_FILE]
        return []

    def playbook(self, name, args, sudo=True):
        if '--nosudo' in args:
            args.pop(args.index('--nosudo'))
            sudo = False

        if sudo:
            args = self.sudo(args)

        cmd = ['ansible-playbook']
        cmd.append('-v')

        cmd += self.inventory()
        cmd += args
        cmd.append(os.path.join(PLAYBOOKS, name))
        cmd = [shlex.quote(i) for i in cmd]

        print(' '.join(cmd))
        res = self.spawn(cmd)

        return res

    def spawn(self, cmd):
        child = pexpect.spawn(' '.join(cmd), encoding='utf8', timeout=300)
        if self.parser.password:
            child.expect('SSH password.*')
            child.sendline(self.parser.password)
            child.expect('SUDO password.*')
            child.sendline(self.parser.password)
        self.interact(child)
        return child.exitstatus

    def interact(self, child):
        if sys.stdout.isatty():
            child.interact()
            child.wait()
        else:
            while child.isalive():
                for i in child.read(1):
                    print(i, end='', flush=True)

    def init(self, target):
        options = [
            '--limit',
            f'{target}',
            '--inventory',
            f'{target},',
        ]

        options += self.parser.options

        return self.playbook('init.yml', options, sudo=False)

    def role(self, name):
        options = self.parser.options
        hosts = self.parser.hosts
        options += ['-e', f'role={name}']

        if hosts:
            options += [
                '--inventory',
                ','.join(hosts) + ',',
                '--limit',
                ','.join(hosts) + ',',
            ]
            playbook = 'role-all.yml'
        else:
            playbook = 'role.yml'

        return self.playbook(playbook, options)

    def package(self, package):
        if sh.which(package):
            return 0

        options = [
            '-c',
            'local',
            '-i',
            'localhost,',
            '-e',
            f'package={package}',
        ]
        user = os.getenv('USER')
        if user != 'root':
            options = self.sudo(options)
        res = self.playbook('package.yml', options)
        if res != 0:
            print('Passing passwords requires sshpass command')
        return res

    def deploy(self):
        options = self.parser.options
        hosts = self.parser.hosts

        if hosts:
            options += [
                '--inventory',
                ','.join(hosts) + ',',
                '--limit',
                ','.join(hosts) + ',',
            ]
            options += ['-e', f'role=project']
            playbook = 'role-all.yml'
        else:
            from ansible.parsing.dataloader import DataLoader
            from ansible.inventory.manager import InventoryManager
            inventory_file_name = INVENTORY_FILE
            data_loader = DataLoader()
            inventory = InventoryManager(
                loader=data_loader,
                sources=[inventory_file_name]
            )
            project_instance = '-'.join([
                self.parser.options_dict['prefix'],
                self.parser.options_dict['instance'],
            ])
            for group, hosts in inventory.get_groups_dict().items():
                if project_instance in group:
                    for host in hosts:
                        hostvars = inventory.get_host(host).vars
                        known_host(hostvars.get('ansible_ssh_host', host))
            playbook = 'project.yml'

        return self.playbook(playbook, options)

    def get_ssh_key(self):
        if INVENTORY_DIR is not None:
            key = os.getenv('SSH_PRIVATE_KEY')
            inv_key = os.path.join(INVENTORY_DIR, 'keys', self.parser.user)
            if key:
                print('Using SSH_PRIVATE_KEY env var')
                self.set_ssh_key(key)
            elif os.path.exists(inv_key):
                print(f'Using {inv_key}')
                with open(inv_key, 'r') as f:
                    for line in f.readlines():
                        if 'ANSIBLE_VAULT' in line:
                            decrypted_vault = self.vault.decrypt(inv_key)
                            self.set_ssh_key(decrypted_vault)
                            break

    def set_ssh_key(self, key):
        with open('.ssh_private_key', 'wb+') as f:
            f.write(key)
        os.chmod('.ssh_private_key', 0o700)
        self.parser.options += ['--private-key', '.ssh_private_key']

    def unset_ssh_key(self):
        if os.path.exists('.ssh_private_key'):
            os.unlink('.ssh_private_key')

    def set_sudo(self):
        if INVENTORY_DIR is not None:
            users = os.path.join(
                        INVENTORY_DIR,
                        os.pardir,
                        'group_vars/all/users.yml'
                    )
            if os.path.exists(users):
                with open(users, 'r') as f:
                    users_data = yaml.load(f.read())

                if not self.parser.checksudo(users_data):
                    # detect that deploy user has no sudo
                    self.parser.options.append('--nosudo')


class Vault(object):
    def __init__(self):
        self.pass_file = None
        self.is_temp = False

    def prepare(self):
        self.pass_file = '.vault'

        if 'ANSIBLE_VAULT_PASSWORD_FILE' in os.environ:
            if not os.path.exists(os.getenv('ANSIBLE_VAULT_PASSWORD_FILE')):
                self.pass_file = os.environ.pop(
                    'ANSIBLE_VAULT_PASSWORD_FILE'
                )

        elif 'ANSIBLE_VAULT_PASSWORD' in os.environ:
            with open(self.pass_file, 'w+') as f:
                f.write(os.getenv('ANSIBLE_VAULT_PASSWORD'))
            self.is_temp = True

        if os.path.exists(self.pass_file):
            os.environ['ANSIBLE_VAULT_PASSWORD_FILE'] = self.pass_file

    def clean(self):
        if self.pass_file:
            os.environ['ANSIBLE_VAULT_PASSWORD_FILE'] = self.pass_file

        # todo: make this safer in a try block or context processor or
        # something
        if self.is_temp:
            os.unlink('.vault')

    def decrypt(self, key):
        print('Decrypting with vault')
        return subprocess.check_output([
            'ansible-vault', 'view', key
        ])
