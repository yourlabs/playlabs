import subprocess

from .exception import PlaylabsCliException


class Ssh(object):
    def __init__(self, parser):
        self.parser = parser
        self.commands = {
            'backup': self.backup,
            'restore': self.restore,
            'log': self.log
        }

    def backup(self):
        if not self.parser.options:
            raise PlaylabsCliException('Backup: Missing container')
        elif len(self.parser.options) > 1:
            raise PlaylabsCliException('Backup: Too many parameters')
        else:
            container = self.parser.options[0]
            subproc_p = [
                'ssh', self.parser.hosts[0],
                f'sudo [ -d /home/{container} ] || exit 1;',
                f'sudo [ -f /home/{container}/backup.sh ] || exit 2;',
                f'sudo /home/{container}/backup.sh',
            ]
            retcode = subprocess.call(subproc_p)
            if retcode == 1:
                raise PlaylabsCliException(
                    f'Backup: container {container} not found'
                )
            elif retcode == 2:
                raise PlaylabsCliException(
                    f'Backup: restore.sh not found'
                )

    def restore(self):
        if not self.parser.options:
            raise PlaylabsCliException('Restore: Missing container')
        else:
            container = self.parser.options[0]
            subproc_p = [
                'ssh', self.parser.hosts[0],
                f'sudo [ -d /home/{container} ] || exit 1;',
                f'sudo [ -f /home/{container}/restore.sh ] || exit 2;',
                f'sudo /home/{container}/restore.sh',
            ] + self.parser.options[1:]
            retcode = subprocess.call(subproc_p)
            if retcode == 1:
                raise PlaylabsCliException(
                    f'Restore: container {container} not found'
                )
            elif retcode == 2:
                raise PlaylabsCliException(
                    f'Restore: restore.sh not found'
                )

    def log(self):
        if not self.parser.options:
            raise PlaylabsCliException('Log: Missing container')
        elif len(self.parser.options) > 1:
            raise PlaylabsCliException('Log: Too many parameters')
        else:
            container = self.parser.options[0]
            subproc_p = [
                'ssh', self.parser.hosts[0],
                f'sudo [ -d /home/{container} ] || exit 1;',
                f'sudo docker logs -f {container}'
            ]
            retcode = subprocess.call(subproc_p)
            if retcode:
                raise PlaylabsCliException(
                    f'Log: container {container} not found'
                )
