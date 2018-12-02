import os

import clitoo
from . import settings
from . import miscellaneous

from .ansible import init, install, deploy # noqa
from .clicmd import help, scaffold # noqa
from .ssh import backup, restore, log # noqa
from .vault import vault


def _cli(*args):
    clitoo.context.default_module = 'playlabs.cli.main'
    clitoo.main(default_path='playlabs.cli.clicmd.help')


def _clitoo_setup():
    vault.prepare()
    miscellaneous.get_ssh_key()
    miscellaneous.set_sudo()


def _clitoo_clean():
    if not os.getenv('PLAYLABS_NOCLEAN'):
        if os.path.exists(settings.KEYPATH):
            os.unlink(settings.KEYPATH)
        vault.clean()


def test(*args, **kwargs):
    print(args)
    print(kwargs)
    print(clitoo.context.args)
    print(clitoo.context.kwargs)
