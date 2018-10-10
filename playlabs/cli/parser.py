import collections
import json
import os

from .exception import PlaylabsCliException


class Parser(object):
    def __init__(self):
        self.handles = {
            'install': self.handle_install,
            'deploy': self.handle_deploy,
            'init': self.handle_init,
            'git': self.handle_git,
            'scaffold': self.handle_scaffold,
            'backup': self.handle_backup,
            'restore': self.handle_restore,
            'log': self.handle_log,
            '-i': self.handle_inventory,
            '-p': self.handle_plugins,
        }
        self.argv = []
        self.primary_tokens = self.handles.keys()
        self._action = None
        self._user = None
        self._password = None
        self.roles = []
        self.hosts = []
        self.options = []
        self.subvars = dict()
        self.options_dict = dict()
        self.argcount = 0

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, name):
        if self._action:
            raise PlaylabsCliException(
                'Only one action can be set:\n' +
                f'Action defined: "{self._action}"\n' +
                f'Current action: "{name}"'
            )
        elif self.password and name != 'init':
            raise PlaylabsCliException(
                'Password only needed for initialization'
            )
        else:
            self._action = name

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, name):
        if self._user:
            raise PlaylabsCliException('User should only be defined once')
        else:
            self._user = name

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        if self.action != 'init':
            raise PlaylabsCliException(
                'Password only needed for initialization'
            )
        else:
            self._password = value

    def handle_scaffold(self):
        self.action = 'scaffold'
        target = self.popargv()
        if target:
            self.options = [target]
        else:
            raise PlaylabsCliException('No target was specified')
        if len(self.argv):
            raise PlaylabsCliException('Too many parameters')

    def handle_git(self):
        self.action = 'git'
        # would be super sweet to prepend git@ to host name in the case of
        # git clone, because that's the username we use on all host git
        # services from github to git.coop
        self.options = self.argv.copy()
        self.argv.clear()

    def handle_install(self):
        self.action = 'install'
        arg = self.popargv()
        if arg:
            self.roles = arg.split(',')
        else:
            raise PlaylabsCliException('No role was specified to install')

    def handle_deploy(self):
        self.action = 'deploy'

    def handle_init(self):
        self.action = 'init'

    def handle_backup(self):
        self.action = 'backup'

    def handle_restore(self):
        self.action = 'restore'

    def handle_log(self):
        self.action = 'log'

    def handle_host(self, arg):
        host = arg.split('@')[-1]
        if host:
            self.hosts.append(host)
        if not arg.startswith('@'):
            left = arg.split('@')[0]
            if ':' in left:
                self.user, self.password = arg.split('@')[0].split(':')
                if '--ask-pass' not in self.options:
                    self.options.append('--ask-pass')

                become = '--ask-become-pass' not in self.options
                if self.user != 'root' and become:
                    self.options.append('--ask-become-pass')
            else:
                self.user = left

        if self.user:
            self.options += ['--user', self.user]

    def handle_inventory(self):
        arg = self.popargv()
        if not arg:
            raise PlaylabsCliException('Inventory: missing parameter')
        for i in arg.split(','):
            if os.path.exists(i):
                self.options += ['-i', i]
            else:
                raise PlaylabsCliException(f'Inventory not found: {i}')
                print(f'command line inventory {i} cannot be found')

    def handle_plugins(self):
        arg = self.popargv()
        if not arg:
            raise PlaylabsCliException('Plugins: missing parameter')
        plugins_path = os.path.join(os.path.dirname(__file__), '../plugins')
        if os.path.exists(plugins_path):
            plugins_list = os.listdir(plugins_path)
            plugins = []
            for p in arg.split(','):
                if p in plugins_list:
                    plugins.append(p)
                else:
                    self.argcount += 1
                    raise PlaylabsCliException(f'Plugin not found: {p}')
            if plugins:
                self.options.append('-e')
                if len(plugins) > 1:
                    self.options.append(f'plugins={",".join(plugins)}')
                else:
                    self.options.append(f'plugins={plugins[0]}')
            else:  # should be useless
                raise PlaylabsCliException(
                    'Plugin: "-p" found but no plugins specified'
                )

    def handle_vars(self, arg):
        if arg == '-e':
            return

        if '=' in arg and not arg.startswith('--'):
            if arg[0] == '=' or arg[-1] == '=':
                raise PlaylabsCliException(
                    f'Wrong variable format {arg}, ' +
                    'variable definition cannot start neither end with "="'
                )
            name = arg.split('=')[0]
            if '.' in name:
                if name[0] == '.' or name[-1] == '.':
                    raise PlaylabsCliException(
                        f'Wrong variable format {name}, ' +
                        'variable name cannot start neither end with "."'
                    )

                def setattribute(a, v):
                    if len(a) > 1:
                        return {a[0]: setattribute(a[1:], v)}
                    else:
                        return {a[0]: v}
                descriptor, val = arg.split('=')
                variable = descriptor.split('.')[0]
                descarray = descriptor.split('.')[1:]
                if variable not in self.subvars.keys():
                    self.subvars[variable] = setattribute(descarray, val)
                else:
                    self.subvars[variable].update(setattribute(descarray, val))
            else:
                self.options += ['-e', arg]
                self.options_dict[name] = arg.split('=')[1]
        else:
            self.options.append(arg)

    def skip(self, arg):
        return

    def ssh_config(self):
        ssh = collections.OrderedDict()

        ssh['ControlMaster'] = 'auto'
        ssh['ControlPersist'] = '60s'
        ssh['ControlPath'] = f'.ssh_control_path_{self.user}'
        ssh['StrictHostKeyChecking'] = 'no'
        self.options += ['--ssh-extra-args', ' '.join([
            f'-o {key}={value}' for key, value in ssh.items()
        ])]

    def popargv(self):
        if len(self.argv):
            self.argcount += 1
            return self.argv.pop(0)

    def parse(self, argv):
        if not argv:
            self.action = 'help'
        else:
            self.argv = argv

        while self.argv:
            arg = self.popargv()

            if arg in self.primary_tokens:
                self.handles[arg]()
            elif arg in ('-u', '--user'):
                self.user = self.popargv()
            elif arg.startswith('-u=') or arg.startswith('--user='):
                self.user = arg.split('=')[-1]
            else:
                if '@' in arg and '=' not in arg:
                    self.handle_host(arg)
                else:
                    self.handle_vars(arg)

        if self.action in ['init', 'install', 'deploy']:
            if not self.user:
                self.user = os.getenv("USER")

            if self.hosts == ['localhost']:
                self.options += ['-c', 'local']
            else:
                self.ssh_config()

            if self.subvars:
                self.options += ['-e', json.dumps(self.subvars)]

        self.print()

    def checksudo(self, data):
        for user in data.get('users'):
            if user['name'] != self.user:
                continue

            roles = user.get('roles', {})
            if 'ssh' in roles:
                if 'sudo' not in roles.get('ssh', []):
                    return False
            else:
                return False
        return True

    def print(self):
        if self.user:
            print(f'Play user: {self.user}')
        if self.hosts:
            print(f'Play hosts: {self.hosts}')
        if self.roles:
            print(f'Play roles: {self.roles}')
        if self.options:
            print(f'Options: {self.options}')
