import os
import re
import shutil
import subprocess
import sys

from .tools import known_host


class Clicmd(object):
    def __init__(self, parser):
        self.parser = parser
        self.commands = {
            'help': self.help,
            'scaffold': self.scaffold,
            'git': self.git
        }

    def help(self):
        helptext = None
        with open(os.path.join(os.path.dirname(__file__), 'help')) as f:
            helptext = f.read()
        print(helptext)

    def scaffold(self):
        target = self.parser.options[0]
        source = None
        if len(self.parser.options) > 1:
            source = self.parser.options[1]

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

    def git(self):
        subprocess.check_output(['git'] + self.parser.options)
