import os
import re
import shutil
import subprocess
import sys

import sh

from .parser import Parser
from .ansible import Ansible
from .tools import known_host

LOCAL_BIN = f'{os.getenv("HOME")}/.local/bin'
LOCAL_BIN_PLAYLABS = f'{LOCAL_BIN}/playlabs'
BASH_PROFILE = f'{os.getenv("HOME")}/.bash_profile'

if '/' in sys.argv[0]:
    os.environ['PATH'] = ':'.join([
        os.path.dirname(sys.argv[0]),
        os.getenv('PATH')
    ])

with open(os.path.join(os.path.dirname(__file__), 'help')) as f:
    HELP = f.read()


def scaffold(target, source):
    if os.path.exists(target):
        print(f'Drop existing {target}?')
        if input().lower() in ['y', 'yes']:
            shutil.rmtree(target)
        else:
            print('Aborting')
            sys.exit(1)

    print(f'Provisioning {target}')
    if not source:
        print(f'From inventory template')
        shutil.copytree(
            os.path.join(
                os.path.dirname(__file__),
                os.pardir,
                'inventory_template',
            ),
            target,
        )
    else:
        print(f'From {source}')
        key = os.getenv('SSH_PRIVATE_KEY')
        if key:
            print('Using SSH_PRIVATE_KEY env var')
            with open('.ssh_private_key', 'w+') as f:
                f.write(key)
            os.chmod('.ssh_private_key', 0o600)

            os.environ['GIT_SSH_COMMAND'] = 'ssh -i .ssh_private_key'

        m = re.match('.*@([^:]*):.*', source)
        if m:
            known_host(m.group(1))

        subprocess.check_output([
            'git',
            'clone',
            source,
            target,
        ])
        if os.path.exists('.ssh_private_key'):
            os.unlink('.ssh_private_key')



def cli():  # noqa
    if len(sys.argv) == 1:
        print(HELP)
        sys.exit(0)
    elif sys.argv[1] == 'scaffold':
        target = os.path.abspath(sys.argv[2])
        scaffold(target, sys.argv[3] if len(sys.argv) > 3 else None)
        sys.exit(0)
    commands = ['scaffold']
    parser = Parser()
    try:
        if sys.argv[1] in commands:
            parser.argcount = 2
            parser.parse(sys.argv[2:])
        else:
            parser.argcount = 1
            parser.parse(sys.argv[1:])
    except Exception as e:
        sys.argv[parser.argcount - 1] += '<---'
        print(f'\nError parsing command line input: {e}\n')
        print(' '.join(sys.argv) + '\n\n')

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

    ansible.vault.prepare()
    ansible.get_ssh_key()
    ansible.set_sudo()

    for host in parser.hosts:
        print(f'Adding {host} to ~/.ssh/known_hosts')
        known_host(host)

    if parser.makedeploy:
        print(f'Deploying project')
        retcode = ansible.deploy()
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
    ansible.unset_ssh_key()
    ansible.vault.clean()

    sys.exit(retcode)
