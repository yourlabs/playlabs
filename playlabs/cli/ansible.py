import collections
import os
import sh

from processcontroller import ProcessController
from . import settings
from . import miscellaneous


class Ansible(object):

    @classmethod
    def inventory(cls):
        if settings.INVENTORY_FILE:
            return ['--inventory', settings.INVENTORY_FILE]
        return []

    @classmethod
    def package(cls, package):
        if sh.which(package):
            return 0

        options = [
            '-c', 'local',
            '-i', 'localhost,',
            '-e', f'package={package}',
        ]
        user = os.getenv('USER')
        if user != 'root':
            cls.sudo(options)
        res = cls.playbook('package.yml', options)
        if res != 0:
            print('Passing passwords requires sshpass command')
        return res

    @classmethod
    def playbook(cls, name, args, sudo=True):
        if '--nosudo' in args:
            args.pop(args.index('--nosudo'))
            sudo = False

        if sudo:
            cls.sudo(args)

        cmd = [sh.which('ansible-playbook')]
        cmd.append('-v')

        cmd += cls.inventory()
        cmd += cls.ssh_config()
        cmd.append(f'--user={settings.USER}')
        cmd += args
        if os.path.exists(settings.KEYPATH):
            cmd.append(f'--private-key={settings.KEYPATH}')
        cmd.append(os.path.join(settings.PLAYBOOKS, name))

        return cls.spawn(cmd)

    @classmethod
    def ssh_config(cls):
        ssh = collections.OrderedDict()

        ssh['ControlMaster'] = 'auto'
        ssh['ControlPersist'] = '60s'
        ssh['ControlPath'] = f'.ssh_control_path_{settings.USER}'
        ssh['StrictHostKeyChecking'] = 'no'
        return ['--ssh-extra-args', ' '.join([
            f'-o {key}={value}' for key, value in ssh.items()
        ])]

    @classmethod
    def spawn(cls, cmd):
        pc_opt = {
                    'echo': False,
                    'private': False,
                    'decode': False,
                    'interactive': True
                }

        if settings.PASSWORD:
            def send_pass(proc, line):
                print(f'sending password {settings.PASSWORD}')
                proc.send(settings.PASSWORD)

            pc_opt['when'] = [
                    ['^(SSH|SUDO|BECOME) password.*: $', send_pass],
            ]

        print(' '.join(cmd))
        proc = ProcessController()
        proc.run(cmd, pc_opt)

        pid, retcode = proc.return_value
        return retcode

    @classmethod
    def sudo(cls, options):
        if '--become' not in options:
            options.append('--become')
        if '--become-method' not in options:
            options += ['--become-method', 'sudo']
        if '--become-user' not in options:
            options += ['--become-user', 'root']

    @classmethod
    def install_sshpass(cls):
        if settings.PASSWORD and not sh.which('sshpass'):
            if cls.package('sshpass'):
                print('Error installing sshpass')


def init(host):
    print('Initializing user (no role argument found)')

    miscellaneous.parse_host(host)
    Ansible.install_sshpass()

    sudo = settings.USER != 'root'
    options = [
        f'--inventory', f'{settings.HOST},',
        f'--limit', f'{settings.HOST},',
    ]
    options += miscellaneous.context_options()

    if settings.PASSWORD:
        if '--ask-pass' not in options:
            options.append('--ask-pass')
        if '--ask-become-pass' not in options and sudo:
            options.append('--ask-become-pass')

    return Ansible.playbook('init.yml', options, sudo)


def install(host, roles):
    print(f'Installing roles {roles}')

    miscellaneous.parse_host(host)
    Ansible.install_sshpass()
    retcode = 0
    for role in roles.split(','):

        options = ['-e', f'role={role}']
        if settings.HOST:
            options += [
                f'--inventory={settings.HOST},',
                f'--limit={settings.HOST},',
            ]
            playbook = 'role-all.yml'
        else:
            playbook = 'role.yml'

        options += miscellaneous.context_options()
        retcode = Ansible.playbook(playbook, options)
        if retcode:
            break

    return retcode


def deploy(host, *args, **kwargs):
    print(f'Deploying project')

    miscellaneous.parse_host(host)
    Ansible.install_sshpass()
    options = []
    if settings.HOST:
        options += [
            f'--inventory={settings.HOST},',
            f'--limit={settings.HOST},',
            '-e', f'role=project',
        ]
        playbook = 'role-all.yml'
    else:
        playbook = 'project.yml'

    options += miscellaneous.context_options(*args, **kwargs)

    return Ansible.playbook(playbook, options)
