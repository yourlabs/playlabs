import os
import yaml

from clitoo import context
from . import settings


def get_ssh_key():
    def _write_ssh_key(key):
        with open(settings.KEYPATH, 'wb+') as f:
            if isinstance(key, str):
                print('Encoding string key to bytes with unicode')
                key = key.encode('utf8')
            f.write(key)
        os.chmod(settings.KEYPATH, 0o700)

    if settings.INVENTORY_DIR and settings.USER:
        inv_key = os.path.join(settings.INVENTORY_DIR, 'keys', settings.USER)
        if os.path.exists(inv_key):
            print(f'Using {inv_key}')
            with open(inv_key, 'r') as f:
                key = f.read()
            if 'ANSIBLE_VAULT' in key:
                decrypted_vault = settings.VAULT.decrypt(inv_key)
                _write_ssh_key(decrypted_vault)
            else:
                _write_ssh_key(key)
            return

    key = os.getenv('SSH_PRIVATE_KEY')
    if key:
        print('Using SSH_PRIVATE_KEY env var')
        _write_ssh_key(key)


def set_sudo():
    if settings.INVENTORY_DIR is not None:
        users = os.path.join(
            settings.INVENTORY_DIR,
            'group_vars/all/users.yml'
        )
        print(f'Looking for users file: {users}')
        if os.path.exists(users):
            with open(users, 'r') as f:
                users_data = yaml.load(f.read())

            for user in users_data.get('users'):
                if user['name'] != settings.USER:
                    continue

                roles = user.get('roles', {})
                if 'ssh' not in roles or 'sudo' not in roles['ssh']:
                    context.args.append('--nosudo')


def parse_host(host):
    if '@' in host:
        user_pass, settings.HOST = host.split('@')
        if ':' in user_pass:
            user, settings.PASSWORD = user_pass.split(':')
            settings.USER = user or settings.USER
    else:
        settings.HOST = host


def context_options():
    options = context.args
    for k, v in context.kwargs:
        options.append(f'{k}={v}')
    return options
