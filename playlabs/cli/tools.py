import os
import re
import subprocess

BASH_PROFILE = f'{os.getenv("HOME")}/.bash_profile'


def known_host(target):
    ssh = f'{os.getenv("HOME")}/.ssh'
    if not os.path.exists(ssh):
        os.makedirs(ssh)
        os.chmod(ssh, 0o700)

    known_hosts = f'{ssh}/known_hosts'
    skip = False
    if os.path.exists(known_hosts):
        with open(known_hosts, 'r') as f:
            for l in f.readlines():
                if re.match('^' + target + ' ', l):
                    skip = True

    if not skip:
        key = subprocess.check_output(['ssh-keyscan', target])
        with open(known_hosts, 'ab+') as f:
            f.write(key)
        os.chmod(known_hosts, 0o600)
