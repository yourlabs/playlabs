import collections
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

import pexpect

import sh

LOCAL_BIN = f'{os.getenv("HOME")}/.local/bin'
LOCAL_BIN_PLAYLABS = f'{LOCAL_BIN}/playlabs'
BASH_PROFILE = f'{os.getenv("HOME")}/.bash_profile'
PLAYBOOKS = os.path.dirname(__file__)

with open(os.path.join(os.path.dirname(__file__), 'help')) as f:
    HELP = f.read()


INVENTORY = None
find = [
    'inventory.yaml',
    'inventory.yml',
    'inventory/inventory.yaml',
    'inventory/inventory.yml',
]
for i in find:
    if os.path.exists(i):
        INVENTORY = i
        break


def patch():
    with open(BASH_PROFILE, 'a+') as f:
        f.write(
            'export PATH=$PATH:$HOME/.local/bin # playlabs'
        )


class Ansible(object):
    def __init__(self, parser):
        os.environ.setdefault('ANSIBLE_STDOUT_CALLBACK', 'yaml')
        self.parser = parser

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
        if INVENTORY:
            return ['--inventory', INVENTORY]

    def playbook(self, name, args, sudo=True):
        if sudo and '--nosudo' not in args:
            args = self.sudo(args)

        cmd = ['ansible-playbook']
        cmd.append('-v')

        cmd += self.inventory()
        cmd += args
        cmd.append(os.path.join(PLAYBOOKS, name))
        cmd = [shlex.quote(i) for i in cmd]

        self.vault_prepare()
        print(' '.join(cmd))
        res = self.spawn(cmd)
        self.vault_restore()

        return res

    def vault_prepare(self):
        self.vault_pass_file = None
        if 'ANSIBLE_VAULT_PASSWORD_FILE' in os.environ:
            if not os.path.exists(os.getenv('ANSIBLE_VAULT_PASSWORD_FILE')):
                self.vault_pass_file = os.environ.pop(
                    'ANSIBLE_VAULT_PASSWORD_FILE'
                )

        elif 'ANSIBLE_VAULT_PASSWORD' in os.environ:
            with open('.vault', 'w+') as f:
                f.write(os.getenv('ANSIBLE_VAULT_PASSWORD'))
            self.remove_vault = True

        if os.path.exists('.vault'):
            os.environ['ANSIBLE_VAULT_PASSWORD_FILE'] = '.vault'

    def vault_restore(self):
        if self.vault_pass_file:
            os.environ['ANSIBLE_VAULT_PASSWORD_FILE'] = self.vault_pass_file

        # todo: make this safer in a try block or context processor or
        # something
        if getattr(self, 'remove_vault', False):
            os.unlink('.vault')

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

        if os.path.exists('inventory.yml'):
            options += ['-i', 'inventory.yml']
        elif os.path.exists('group_vars') or os.path.exists('host_vars'):
            options += ['-i', '.']

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


class Parser(object):
    def __init__(self):
        self.handles = {
            'install': self.handle_install,
            'deploy': self.handle_deploy,
            'init': self.handle_init,
            '-i': self.handle_inventory,
            '-p': self.handle_plugins,
        }
        self.primary_tokens = self.handles.keys()
        self.makeinstall = False
        self.makedeploy = False
        self.makeinit = False
        self.roles = []
        self.hosts = []
        self.options = []
        self.password = None
        self.subvars = dict()

    def handle_install(self, arg):
        if arg:
            self.makeinstall = True
            self.roles = arg.split(',')
        else:
            print('no role to install')

    def handle_deploy(self, arg):
        self.makedeploy = True

    def handle_init(self, arg):
        self.makeinit = True

    def handle_host(self, arg):
        self.hosts.append(arg.split('@')[-1])
        if not arg.startswith('@'):
            left = arg.split('@')[0]
            if ':' in left:
                self.user, self.password = arg.split('@')[0].split(':')
                if '--ask-become-pass' not in self.options:
                    self.options.append('--ask-become-pass')
                    self.options.append('--ask-pass')
            else:
                self.user = left
        else:
            self.user = os.getenv("USER")

        if getattr(self, 'user', False):
            self.options.append(f'--user={self.user}')

    def handle_inventory(self, arg):
        for i in arg.split(','):
            if os.path.exists(i):
                self.options += ['-i', i]
            else:
                print(f'command line inventory {i} cannot be found')

    def handle_plugins(self, arg):
        plugins_path = os.path.join(os.path.dirname(__file__), 'plugins')
        if os.path.exists(plugins_path):
            plugins_list = os.listdir(plugins_path)
            plugins = []
            for p in arg.split(','):
                if p in plugins_list:
                    plugins.append(p)
                else:
                    print(f'command line plugin {p} cannot be found')
            if plugins:
                self.options.append('-e')
                if len(plugins) > 1:
                    self.options.append(f'plugins={",".join(plugins)}')
                else:
                    self.options.append(f'plugins={plugins[0]}')
            else:
                print('no plugins specified')

    def handle_vars(self, arg):
        if arg == '-e':
            return

        if '=' in arg and not arg.startswith('--'):
            if '.' in arg.split('=')[0]:
                descriptor, value = arg.split('=')
                variable, attribute = descriptor.split('.')
                self.subvars[attribute] = value
            else:
                self.options += ['-e', arg]
        else:
            self.options.append(arg)

    def skip(self, arg):
        return

    def parse(self, args):
        ssh = collections.OrderedDict()

        while args:
            arg = args.pop(0)
            if '@' in arg and '=' not in arg:
                self.handle_host(arg)
            elif arg in ['init', 'deploy']:
                self.handles[arg](None)
            elif arg in self.primary_tokens:
                self.handles[arg](args.pop(0) if args else None)
            else:
                self.handle_vars(arg)

        if self.hosts == ['localhost']:
            self.options += ['-c', 'local']
        else:
            ssh['ControlMaster'] = 'auto'
            ssh['ControlPersist'] = '60s'
            ssh['ControlPath'] = '.ssh_control_path'
            self.options += ['--ssh-extra-args', ' '.join([
                f'-o {key}={value}' for key, value in ssh.items()
            ])]

        if self.subvars:
            self.options += ['-e', json.dumps(self.subvars)]

        self.print()

    def print(self):
        if self.hosts:
            print(f'Play hosts: {self.hosts}')
        if self.roles:
            print(f'Play roles: {self.roles}')
        if self.options:
            print(f'Options: {self.options}')


def scaffold(target):
    if os.path.exists(target):
        print(f'Drop existing {target}?')
        if input().lower() in ['y', 'yes']:
            shutil.rmtree(target)
        else:
            print('Aborting')
            sys.exit(1)
    print(f'Provisioning {target}')
    shutil.copytree(
        os.path.join(
            os.path.dirname(__file__),
            'inventory_template',
        ),
        target,
    )
    # ask to confirm init maybe?
    print(f'{target} ready ! run playlabs in there to execute')


def known_host(target):
    ssh = f'{os.getenv("HOME")}/.ssh'
    if not os.path.exists(ssh):
        os.makedirs(ssh)
        os.chmod(ssh, 0o700)

    known_hosts = f'{ssh}/known_hosts'
    skip = False
    if os.path.exists(known_hosts):
        with open(known_hosts, 'r') as f:
            for l in f.readlines():
                if re.match('^' + target + ' ', l):
                    skip = True

    if not skip:
        key = subprocess.check_output(['ssh-keyscan', target])
        with open(known_hosts, 'ab+') as f:
            f.write(key)
        os.chmod(known_hosts, 0o600)


def cli():  # noqa
    if len(sys.argv) == 1:
        print(HELP)
        sys.exit(0)
    elif sys.argv[1] == 'scaffold':
        target = os.path.abspath(sys.argv[2])
        scaffold(target)
        sys.exit(0)
    commands = ['scaffold']
    parser = Parser()
    if sys.argv[1] in commands:
        parser.parse(sys.argv[2:])
    else:
        parser.parse(sys.argv[1:])

    # todo: check if connection works with provided credentials if any
    # otherwise try without credentials, and strip them from now on
    # because that would mean that the host is already initped
    # meanwhile, it fails with root@ ... Permission denied because
    # we disable root login in ssh role

    ansible = Ansible(parser)
    retcode = 0
    if parser.password and not sh.which('sshpass'):
        retcode = ansible.package('sshpass')
        if retcode:
            return retcode

    key = os.getenv('SSH_PRIVATE_KEY')
    inventory_key = os.path.join(INVENTORY, 'keys', parser.user)
    if key:
        print('Using SSH_PRIVATE_KEY env var')
        with open('.ssh_private_key', 'w+') as f:
            f.write(key)
        parser.options += ['--private-key', '.ssh_private_key']
    elif os.path.exists(inventory_key):
        print(f'Using {inventory_key}')
        decrypt = False
        with open(key, 'r') as f:
            for line in f.readlines():
                if 'ANSIBLE_VAULT' in line:
                    decrypt = True
                    break
        if decrypt:
            print('Decrypting with vault')
            out = subprocess.check_output([
                'ansible-vault', 'view', inventory_key
            ])
            with open('.ssh_private_key', 'wb+') as f:
                f.write(out)
            parser.options += ['--private-key', '.ssh_private_key']
        else:
            print(f'Using {key}')
            parser.options += ['--private-key', key]

    for host in parser.hosts:
        print(f'Adding {host} to ~/.ssh/known_hosts')
        known_host(host)

    if parser.makedeploy:
        print(f'Deploying with project role')
        retcode = ansible.role('project')
        if retcode:
            return retcode

    elif parser.makeinit:
        print('Initializing user (no role argument found)')
        for host in parser.hosts:
            retcode = ansible.init(host)
            if retcode:
                sys.exit(retcode)

    elif parser.makeinstall:
        print(f'Installing roles {",".join(parser.roles)}')
        for role in parser.roles:
            retcode = ansible.role(role)
            if retcode:
                sys.exit(retcode)
    elif sys.argv[1] == 'backup':
        subprocess.call([
            'ssh',
            parser.hosts[0],
            'sudo',
            '/home/' + sys.argv[3] + '/backup.sh'
        ])
    elif sys.argv[1] == 'restore':
        subprocess.call([
            'ssh',
            parser.hosts[0],
            'sudo',
            '/home/' + sys.argv[3] + '/restore.sh',
        ] + sys.argv[4:])
    elif sys.argv[1] == 'log':
        subprocess.call([
            'ssh',
            parser.hosts[0],
            'sudo',
            'docker',
            'logs',
            '-f',
            sys.argv[3]
        ])

    # todo: wrap the whole thing in a try block to ensure cleaning
    if os.path.exists('.ssh_private_key'):
        os.unlink('.ssh_private_key')

    sys.exit(retcode)
