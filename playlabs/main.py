import click
import os
import sh
import shlex
import subprocess
import sys


os.environ['PATH'] = f'{os.getenv("PATH")}:{os.getenv("HOME")}/.local/bin'


class Ansible(object):
    def __init__(
        self,
        inventory,
        playbooks,
        user,
        debug,
    ):
        self.inventory = os.path.abspath(inventory)
        self.playbooks = os.path.abspath(playbooks)
        self.user = user
        self.debug = debug

    def playbook(self, name, options):
        cmd = ['ansible-playbook']
        for key, value in options.items():
            if value is True:
                cmd.append(key)
            else:
                cmd.append(f'{key}={value}')
        cmd.append('-v')
        cmd.append(os.path.join(self.playbooks, 'bootstrap.yml'))
        cmd = shlex.split(' '.join(cmd))

        vault_pass_file = os.environ.pop('ANSIBLE_VAULT_PASSWORD_FILE')
        os.environ['ANSIBLE_STDOUT_CALLBACK'] = 'debug'
        r = subprocess.call(cmd)
        if vault_pass_file:
            os.environ['ANSIBLE_VAULT_PASSWORD_FILE'] = vault_pass_file
        return r


@click.group()
@click.option('--inventory',
    envvar='INVENTORY',
    default='.'
)
@click.option('--playbooks',
    envvar='PLAYBOOKS',
    default=os.path.dirname(__file__),
)
@click.option('--user',
    envvar='USER'
)
@click.option('--debug/--no-debug',
    default=False,
    envvar='DEBUG'
)
@click.pass_context
def cli(
    ctx,
    inventory,
    playbooks,
    user,
    debug
):
    ctx.obj = Ansible(
        inventory,
        playbooks,
        user,
        debug
    )


@cli.command()
@click.argument('target')
@click.pass_obj
def bootstrap(ansible, target):
    user, host = target.split('@')

    options = {
        '--user': user
    }
    if user != 'root':
        options['--become'] = True
        options['--become-method'] = 'sudo'
        options['--become-user'] = 'root'
    options['--inventory'] = f'"{host},"'

    sys.exit(ansible.playbook('bootstrap.yml', options))
