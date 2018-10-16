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

    def check_retcode(self, code, c):
        name = self.parser.action.capitalize()
        if code == 1:
            raise PlaylabsCliException(
                f'{name}: container {c} not found'
            )
        elif code == 2:
            raise PlaylabsCliException(
                f'{name}: file {self.parser.action}.sh not found'
            )
        elif code == 255:
            raise PlaylabsCliException(
                f'{name}: SSH error'
            )
        elif code:
            raise PlaylabsCliException(
                f'{name}: Uknown error ({code})'
            )

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
            self.check_retcode(retcode, container)

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
            self.check_retcode(retcode, container)

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
            self.check_retcode(retcode, container)
