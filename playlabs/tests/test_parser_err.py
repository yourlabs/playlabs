"""
##### ERROR CASES #####

 user cannot be defined twice
 vars cannot start with '.'
 nothing can start with '='
 plugins must exist
 plugins must be specified
 inventory file must exist
 inventory must be specified

[LATER] host must be found either in CLI or in inventories
"""

from playlabs.cli.parser import Parser

import pytest


@pytest.fixture
def p():
    return Parser()


def test_multi_user_error(p):
    with pytest.raises(Exception):
        p.parse(['-u', 'user1', '-u', 'user2'])


def test_multi_user_error_at(p):
    with pytest.raises(Exception):
        p.parse(['-u', 'user1', 'user@host'])


def test_var_starting_with_eq(p):
    with pytest.raises(Exception):
        p.parse(['=value'])


def test_var_ending_with_eq(p):
    with pytest.raises(Exception):
        p.parse(['var='])


def test_var_starting_with_dot(p):
    with pytest.raises(Exception):
        p.parse(['.var=value'])


def test_var_ending_with_dot(p):
    with pytest.raises(Exception):
        p.parse(['var.=value'])


def test_plugin_must_exits(p):
    with pytest.raises(Exception):
        p.parse(['-p', 'notaplugin'])


def test_plugin_must_be_specified(p):
    with pytest.raises(Exception):
        p.parse(['-p'])


def test_inventory_must_exist(p):
    with pytest.raises(Exception):
        p.parse(['-i', 'inexistant13245.yml'])


def test_inventory_must_be_specified(p):
    with pytest.raises(Exception):
        p.parse(['-i'])
