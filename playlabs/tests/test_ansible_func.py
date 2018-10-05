"""
##### PARAMETERS #####

"""

from playlabs.cli.ansible import Ansible
from playlabs.cli.parser import Parser

import pytest


@pytest.fixture
def p():
    return Parser()


@pytest.fixture
def a(p):
    return Ansible(p)


def test_ansible_sudo(a):
    assert a.sudo([]) == [
        '--become',
        '--become-method', 'sudo',
        '--become-user', 'root'
    ]


def test_ansible_inventory(a):
    a.INVENTORY_FILE = 'filename.yml'
    i = a.inventory()
    assert i == ['--inventory', 'filename.yml']
