import os
import shutil
import subprocess
import sys


class Clicmd(object):
    def __init__(self, parser):
        self.parser = parser
        self.commands = {
            'help': self.help,
            'scaffold': self.scaffold,
            'git': self.git
        }
        self.key_path = '.ssh_private_key'

    def help(self):
        helptext = None
        with open(os.path.join(os.path.dirname(__file__), 'help.txt')) as f:
            helptext = f.read()
        print(helptext)

    def scaffold(self):
        target = self.parser.options[0]

        if os.path.exists(target):
            print(f'Drop existing {target}?')
            if input().lower() in ['y', 'yes']:
                shutil.rmtree(target)
            else:
                print('Aborting')
                sys.exit(1)

        print(f'Provisioning {target} from inventory template')
        shutil.copytree(
            os.path.join(
                os.path.dirname(__file__),
                os.pardir,
                'inventory_template',
            ),
            target,
        )

    def git(self):
        key = os.getenv('SSH_PRIVATE_KEY')
        if key:
            print('Using SSH_PRIVATE_KEY env var')
            with open(self.key_path, 'w+') as f:
                f.write(key)
            os.chmod(self.key_path, 0o600)

            os.environ['GIT_SSH_COMMAND'] = ' '.join((
                f'ssh -i {self.key_path}',
                '-o StrictHostKeyChecking=no'
            ))

        subprocess.check_output(['git'] + self.parser.options)

        if os.path.exists(self.key_path):
            os.unlink(self.key_path)
