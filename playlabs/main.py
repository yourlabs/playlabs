import click
import os
import re
import sh
import shlex
import subprocess
import sys


LOCAL_BIN = f'{os.getenv("HOME")}/.local/bin'
LOCAL_BIN_PLAYLABS = f'{LOCAL_BIN}/playlabs'
BASH_PROFILE = f'{os.getenv("HOME")}/.bash_profile'

if os.path.abspath(sys.argv[0]) == LOCAL_BIN_PLAYLABS:
    if LOCAL_BIN not in os.getenv('PATH').split(':'):
        if os.path.exists(BASH_PROFILE):
            with open(BASH_PROFILE, 'r') as f:
                res = f.read()
            if '# playlabs' not in res:
                result = click.confirm(
                    'Patch ~/.local/bin in ~/.bash_profile $PATH ?',
                    default=True,
                )
                if result:
                    with open(BASH_PROFILE, 'a+') as f:
                        f.write(
                            'export PATH=$PATH:$HOME/.local/bin # playlabs'
                        )
                else:
                    with open(BASH_PROFILE, 'a+') as f:
                        f.write('# playlabs')

os.environ['PATH'] = f'{os.getenv("PATH")}:'


class Ansible(object):
    def __init__(
        self,
        inventory,
        playbooks,
    ):
        self.inventory = os.path.abspath(inventory)
        self.playbooks = os.path.abspath(playbooks)

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


    def playbook(self, name, args):
        cmd = ['ansible-playbook']
        cmd.append('-v')
        cmd += args
        cmd.append(os.path.join(self.playbooks, name))
        cmd = shlex.split(' '.join(cmd))

        vault_pass_file = None
        if 'ANSIBLE_VAULT_PASSWORD_FILE' in os.environ:
            vault_pass_file = os.environ.pop('ANSIBLE_VAULT_PASSWORD_FILE')
        os.environ['ANSIBLE_STDOUT_CALLBACK'] = 'debug'
        click.echo(' '.join(cmd))
        r = subprocess.call(cmd)
        if vault_pass_file:
            os.environ['ANSIBLE_VAULT_PASSWORD_FILE'] = vault_pass_file
        return r

    def bootstrap(self, target, extra_args):
        user, host = target.split('@')
        if not user:
            user = os.getenv('USER')

        options = [
            f'--user={user}'
        ]
        if user != 'root':
            options = self.sudo(options)
        options += ['--inventory', f'"{host},"'] + extra_args

        return ansible.playbook('bootstrap.yml', options)

    def role(self, name, extra_args):
        playbook = 'role.yml'
        options = ['-e', f'role={name}']
        targets = []

        noroot = False
        for arg in extra_args:
            if re.match('^@[\w\d_.-]*$', arg):
                targets.append(arg[1:])
            elif arg == '--noroot':
                noroot = True
            else:
                options.append(arg)

        if not noroot:
            options = self.sudo(options)

        if targets:
            options += ['-i ' + ','.join(targets) + ',']
            playbook = 'role-all.yml'

        tasks = os.path.join(os.path.dirname(__file__), 'roles', name, 'tasks', 'main.yml')
        next_role = None
        if os.path.exists(tasks):
            with open(tasks, 'r') as f:
                for line in f.readlines():
                    if not line.startswith('# playlabs '):
                        continue

                    line = line[len('# playlabs '):].strip()
                    option, value = line.split('=')

                    if option == 'next':
                        next_role = value
        retcode = ansible.playbook(playbook, options)
        if retcode != 0:
            return retcode

        if next_role:
            res = click.confirm(
                f'Do you want to execute next role {next_role} ?',
                default=True,
            )
            if res:
                retcode = self.role(next_role, extra_args)

        return retcode

ansible = Ansible(
    '.',
    os.path.dirname(__file__),
)


def cli():
    if '@' in sys.argv[1]:
        sys.exit(ansible.bootstrap(sys.argv[1], sys.argv[2:]))
    elif ',' in sys.argv[1]:
        for role in sys.argv[1].split(','):
            retcode = ansible.role(role, sys.argv[2:])
            if retcode != 0:
                sys.exit(retcode)
        sys.exit(0)
    else:
        sys.exit(ansible.role(sys.argv[1], sys.argv[2:]))
