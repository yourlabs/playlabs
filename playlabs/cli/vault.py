import os
import subprocess


class _Vault(object):
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


vault = _Vault()
