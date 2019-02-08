import os
import shlex
import subprocess
import sys

import pexpect

import sh

import yaml

find = [
    'inventory.yaml',
    'inventory.yml',
    'inventory/inventory.yaml',
    'inventory/inventory.yml',
]


class Ansible(object):
    def __init__(self, parser):
        os.environ.setdefault('ANSIBLE_STDOUT_CALLBACK', 'yaml')
        self.commands = {
            'init': self.init,
            'deploy': self.deploy,
            'install': self.install
        }
        self.parser = parser
        self.vault = Vault()
        self.PLAYBOOKS = os.path.join(
            os.path.dirname(__file__),
            os.pardir
        )
        self.key_path = '.ssh_private_key'

        self.INVENTORY_FILE = None
        self.INVENTORY_DIR = None
        for i in find:
            if os.path.exists(i):
                self.INVENTORY_FILE = os.path.abspath(i)
                self.INVENTORY_DIR = os.path.abspath(
                    os.path.dirname(self.INVENTORY_FILE)
                )
                break

    def __str__(self):
        return 'Ansible'

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
        if self.INVENTORY_FILE:
            return ['--inventory', self.INVENTORY_FILE]
        return []

    def playbook(self, name, args, sudo=True):
        if '--nosudo' in args:
            args.pop(args.index('--nosudo'))
            sudo = False

        if sudo:
            args = self.sudo(args)

        os.environ['ANSIBLE_REMOTE_TMP'] = (
            f'/tmp/.ansible-{self.parser.user}')

        cmd = ['ansible-playbook']
        cmd.append('-v')
        cmd += self.inventory()
        cmd += args
        if os.path.exists(self.key_path):
            cmd += ['--private-key', self.key_path]
        cmd += ['-e', 'ansible_python_interpreter=/usr/bin/python3']
        if 'k8s' in self.parser.roles:
            cmd += ['-e', 'docker_package="docker-ce=18.06.1~ce~3-0~ubuntu"']
        cmd.append(os.path.join(self.PLAYBOOKS, name))
        cmd = [shlex.quote(i) for i in cmd]

        print(' '.join(cmd))
        res = self.spawn(cmd)

        return res

    def spawn(self, cmd):
        child = pexpect.spawn(' '.join(cmd), encoding='utf8', timeout=3600)
        if self.parser.password:
            child.expect('SSH password.*')
            child.sendline(self.parser.password)

            if self.parser.user != 'root':
                child.expect('BECOME password.*')
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

    def prepare_init(self):
        init_options_array = []
        for host in self.parser.hosts:
            options = self.parser.options + [
                '--inventory',
                f'{host},',
                '--limit',
                f'{host}',
            ]
            init_options_array.append(
                [
                    'init.yml',
                    options,
                    self.parser.user != 'root'
                ]
            )
        return init_options_array

    def prepare_install(self):
        install_options_array = []
        for role in self.parser.roles:
            task = None
            if '/' in role:
                role, task = role.split('/')

            if '.' in role:
                # is the role installed ?
                out = subprocess.check_output([
                    'ansible-galaxy', 'list', role
                ])
                if b'not found' in out:
                    print(subprocess.check_output([
                        'ansible-galaxy', 'install', role
                    ]))

            options = self.parser.options + ['-e', f'role={role}']

            if self.parser.hosts:
                options += [
                    '--inventory',
                    ','.join(self.parser.hosts) + ',',
                    '--limit',
                    ','.join(self.parser.hosts) + ',',
                ]

                if self.parser.hosts == ['192.168.168.168']:
                    # compensate for vagrant
                    options += [
                        '-e',
                        ' '.join([
                            '{"ansible_default_ipv4":',
                            '{"address": "192.168.168.168"}}',
                        ])
                    ]

                if task:
                    playbook = 'role-task-all.yml'
                    options += ['-e', f'playlabs_task={task}']
                else:
                    playbook = 'role-all.yml'
            else:
                playbook = 'role.yml'

            install_options_array.append([playbook, options, True])
        return install_options_array

    def prepare_deploy(self):
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
            playbook = 'project.yml'
        return [[playbook, options, True]]

    def init(self):
        print('Initializing user (no role argument found)')
        return self.compute(self.prepare_init)

    def install(self):
        print(f'Installing roles {",".join(self.parser.roles)}')
        return self.compute(self.prepare_install)

    def deploy(self):
        print(f'Deploying project')
        return self.compute(self.prepare_deploy)

    def compute(self, prepare_func):
        options_array = prepare_func()
        for playbook, options, sudo in options_array:
            retcode = self.playbook(playbook, options, sudo)
            if retcode:
                return retcode

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

    def get_ssh_key(self):
        if self.INVENTORY_DIR and self.parser.user:
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

    def set_sudo(self):
        if self.INVENTORY_DIR is not None:
            users = os.path.join(
                self.INVENTORY_DIR,
                'group_vars/all/users.yml'
            )
            print(f'Looking for users file: {users}')
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
