import subprocess

from .exception import PlaylabsCliException


def _check_retcode(name, code, c):
    if code == 1:
        raise PlaylabsCliException(
            f'{name}: container {c} not found'
        )
    elif code == 2:
        raise PlaylabsCliException(
            f'{name}: file {name}.sh not found'
        )
    elif code == 255:
        raise PlaylabsCliException(
            f'{name}: SSH error'
        )
    elif code:
        raise PlaylabsCliException(
            f'{name}: Uknown error ({code})'
        )


def _exec(host, container, script):
    subproc_p = [
        'ssh', host,
        f'sudo [ -d /home/{container} ] || exit 1;',
    ]

    if script == 'log':
        subproc_p += f'sudo docker logs -f {container}'
    else:
        subproc_p += [
            f'sudo [ -f /home/{container}/{script}.sh ] || exit 2;',
            f'sudo /home/{container}/{script}.sh',
        ]

    _check_retcode(script, subprocess.call(subproc_p), container)


def backup(host, container):
    _exec(host, container, 'backup')


def restore(host, container):
    _exec(host, container, 'restore')


def log(host, container):
    _exec(host, container, 'log')
