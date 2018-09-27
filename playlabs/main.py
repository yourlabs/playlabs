import os
import shlex
import shutil
import sys
import pexpect
import sh

LOCAL_BIN = f'{os.getenv("HOME")}/.local/bin'
LOCAL_BIN_PLAYLABS = f'{LOCAL_BIN}/playlabs'
BASH_PROFILE = f'{os.getenv("HOME")}/.bash_profile'
PLAYBOOKS = os.path.dirname(__file__)

with open(os.path.join(os.path.dirname(__file__), 'help')) as f:
    HELP = f.read()


def patch():
    with open(BASH_PROFILE, 'a+') as f:
        f.write(
            'export PATH=$PATH:$HOME/.local/bin # playlabs'
        )

if os.path.abspath(sys.argv[0]) == LOCAL_BIN_PLAYLABS:
    if LOCAL_BIN not in os.getenv('PATH').split(':'):
        if not os.path.exists(BASH_PROFILE):
            patch()
        else:
            with open(BASH_PROFILE, 'r') as f:
                res = f.read()
            if '# playlabs' not in res:
                result = click.confirm(
                    'Patch ~/.local/bin in ~/.bash_profile $PATH ?',
                    default=True,
                )
                if result:
                    patch()
                else:
                    with open(BASH_PROFILE, 'a+') as f:
                        f.write('# playlabs')

os.environ['PATH'] = f'{os.getenv("PATH")}:'


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

    def playbook(self, name, args, sudo=True):
        if sudo and '--nosudo' not in args:
            args = self.sudo(args)
        cmd = ['ansible-playbook']
        cmd.append('-v')
        find = [
            'inventory.yaml',
            'inventory.yml',
            'inventory/inventory.yaml',
            'inventory/inventory.yml',
        ]
        for i in find:
            if os.path.exists(i):
                cmd += ['--inventory', i]
        cmd += args
        cmd.append(os.path.join(PLAYBOOKS, name))
        cmd = [shlex.quote(i) for i in cmd]

        vault_pass_file = None
        if 'ANSIBLE_VAULT_PASSWORD_FILE' in os.environ:
            if not os.path.exists(os.getenv('ANSIBLE_VAULT_PASSWORD_FILE')):
                vault_pass_file = os.environ.pop('ANSIBLE_VAULT_PASSWORD_FILE')
        print(' '.join(cmd))

        res = self.spawn(cmd)
        if vault_pass_file:
            os.environ['ANSIBLE_VAULT_PASSWORD_FILE'] = vault_pass_file
        return res

    def spawn(self, cmd):
        child = pexpect.spawn(' '.join(cmd), encoding='utf8', timeout=300)
        if self.parser.password:
            child.expect('SSH password.*')
            child.sendline(self.password)
            child.expect('SUDO password.*')
            child.sendline(self.password)
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

    def bootstrap(self, target):
        user = None

        if '@' in target:
            user, self.parser.host = target.split('@')
        else:
            self.parser.host = target

        if not user:
            user = os.getenv('USER')

        options = [
            f'--user={user}',
            '--limit',
            f'{parser.host},',
            '--inventory',
            f'{parser.host},',
        ]

        options += self.parser.options

        return self.playbook('bootstrap.yml', options, sudo=False)

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
        self.primary_tokens = ['-h', '-r', '-u', '-i', '-p']
        self.handles = {
            '-h': self.handle_hosts,
            '-r': self.handle_roles,
            '-u': self.handle_user,
            '-i': self.handle_inventory,
            '-p': self.handle_plugins,
        }
        self.hosts = []
        self.roles = []
        self.options = []
        self.password = None

    def handle_hosts(self, arg):
        self.hosts += arg.split(',')
   
    def handle_roles(self, arg):
        self.roles += arg.split(',')

    def handle_user(self, arg):
        if ':' in arg:
            user, self.password = arg.split(':')
            if not '--ask-become-pass' in self.options:
                self.options.append('--ask-become-pass')
                self.options.append('--ask-pass')
        else:
            user = arg
        if '--user' in self.options:
            print(f'command line user already set, overriding by {user}')
            self.options[self.options.index('--user') + 1] = user
        else:
            self.options += ['--user', user]

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
                print('command line -p option set but no available plugins specified')


    def handle_vars(self, arg):
        if arg == '-e':
            return
        if '=' in arg:
            self.options += ['-e', arg]
        else:
            self.options.append(arg)

    def skip(self, arg):
        return

    def hostparse(self, arg):
        self.hosts.append(arg.split('@')[-1])
        if not arg.startswith('@'):
            left = arg.split('@')[0]
            self.handle_user(left)

    def parse(self, args):
        while args:
            arg = args.pop(0)
            if args == '--nostrict':
                self.options = nostrict(options)
            elif '@' in arg:
                self.hostparse(arg)
            elif arg in self.primary_tokens:
                self.handles[arg](args.pop(0))
            else:
                self.handle_vars(arg)

        if self.hosts == ['localhost']:
            self.options += ['-c', 'local']

        if self.hosts:
            print(f'Play hosts: {self.hosts}')
        if self.roles:
            print(f'Play roles: {self.roles}')
        if self.options:
            print(f'Options: {self.options}')


def init(target):
    if os.path.exists(target):
        if click.confirm(f'Drop existing {target}?', default=False):
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
    #ask to confirm bootstrap maybe?
    print(f'{target} ready ! run playlabs in there to execute')


def nostrict(options):
    options += [
        '--ssh-extra-args',
        '-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no',
    ]
    return options


def cli():
    if len(sys.argv) == 1:
        print(HELP)
        sys.exit(0)
    elif sys.argv[1] == 'init':
        target = os.path.abspath(sys.argv[2])
        init(target)
        sys.exit(0)
    parser = Parser()
    parser.parse(sys.argv[2:])

    # todo: check if connection works with provided credentials if any
    # otherwise try without credentials, and strip them from now on
    # because that would mean that the host is already bootstrapped
    # meanwhile, it fails with root@ ... Permission denied because
    # we disable root login in ssh role

    ansible = Ansible(parser)
    retcode = 0
    if parser.password and not sh.which('sshpass'):
        retcode = ansible.package('sshpass')
        if retcode:
            return retcode

    if sys.argv[1] == 'deploy':
        retcode = ansible.role('project')
        if retcode:
            return retcode
        
    elif sys.argv[1] == 'bootstrap':
        print('Bootstrapping (no role argument found)')
        for host in parser.hosts:
            retcode = ansible.bootstrap(host)
            if retcode:
                sys.exit(retcode)
    elif sys.argv[1] == 'install':
        print(f'Applying {",".join(roles)}')
        for role in roles:
            retcode = ansible.role(role)
            if retcode:
                sys.exit(retcode)
    elif sys.argv[1] == 'backup':
        print('not available yet')
    elif sys.argv[1] == 'restore':
        print('not available yet')
    elif sys.argv[1] == 'log':
        print('not available yet')

    sys.exit(retcode)
