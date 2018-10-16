import os
import sys

import sh

from .ansible import Ansible
from .clicmd import Clicmd
from .exception import PlaylabsCliException
from .parser import Parser
from .ssh import Ssh

LOCAL_BIN = f'{os.getenv("HOME")}/.local/bin'
LOCAL_BIN_PLAYLABS = f'{LOCAL_BIN}/playlabs'
BASH_PROFILE = f'{os.getenv("HOME")}/.bash_profile'

if '/' in sys.argv[0]:
    os.environ['PATH'] = ':'.join([
        os.path.dirname(sys.argv[0]),
        os.getenv('PATH')
    ])


def cli():  # noqa
    parser = Parser()
    try:
        parser.parse(sys.argv[1:])
    except PlaylabsCliException as e:
        sys.argv[parser.argcount] += '<---'
        print(f'\nError parsing command line input: {e}\n')
        print(' '.join(sys.argv) + '\n\n')

    # todo: check if connection works with provided credentials if any
    # otherwise try without credentials, and strip them from now on
    # because that would mean that the host is already initped
    # meanwhile, it fails with root@ ... Permission denied because
    # we disable root login in ssh role

    clicmd = Clicmd(parser)
    ansible = Ansible(parser)
    ssh = Ssh(parser)

    retcode = 0
    if parser.password and not sh.which('sshpass'):
        retcode = ansible.package('sshpass')
        if retcode:
            print('Error installing sshpass')

    ansible.vault.prepare()
    ansible.get_ssh_key()
    ansible.set_sudo()

    # we have ssh options working for that no ?
    # for host in parser.hosts:
    #    print(f'Adding {host} to ~/.ssh/known_hosts')
    #    known_host(host)

    for module in [clicmd, ansible, ssh]:
        if parser.action in module.commands.keys():
            try:
                retcode = module.commands[parser.action]()
            except PlaylabsCliException as e:
                retcode = 1
                print(e)

    if not os.getenv('PLAYLABS_NOCLEAN'):
        ansible.unset_ssh_key()
        ansible.vault.clean()
    sys.exit(retcode)
