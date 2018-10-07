"""
##### PARAMETERS #####

 test -u,--user username[:password], -u=username, --user=username
 test default_user
 test [username[:password]]@host
 test localhost options
 test ssh_config
 test vars, subvars, ansible options
 test roles
 test inventories
 test plugins
"""

import json
import os

from playlabs.cli.parser import Parser

import pytest


@pytest.fixture
def p():
    return Parser()


def test_parser_class_exists(p):
    assert p


def test_user_name_shortopt(p):
    p.parse(['init', '-u', 'testname'])
    assert p.user == 'testname'


def test_user_name_longopt(p):
    p.parse(['init', '--user', 'testname2'])
    assert p.user == 'testname2'


def test_user_name_shortvar(p):
    p.parse(['init', '-u=testname1'])
    assert p.user == 'testname1'


def test_user_name_longvar(p):
    p.parse(['init', '--user=testname2'])
    assert p.user == 'testname2'


def test_user_default(p):
    p.parse(['init'])
    assert p.user == os.getenv('USER')


def test_at_host_only(p):
    p.parse(['init', '@testhost'])
    assert p.hosts == ['testhost']


def test_user_at_host(p):
    p.parse(['init', 'testname3@testhost2'])
    assert p.user == 'testname3'
    assert p.hosts == ['testhost2']


def test_user_pass_at_host(p):
    p.parse(['init', 'testname4:password@testhost3'])
    assert p.user == 'testname4'
    assert p.hosts == ['testhost3']
    assert p.password == 'password'
    assert '--ask-become-pass' in p.options
    assert '--ask-pass' in p.options


def test_root_pass_at_host(p):
    p.parse(['init', 'root:password@testhost3'])
    assert p.user == 'root'
    assert p.hosts == ['testhost3']
    assert p.password == 'password'
    assert '--ask-become-pass' not in p.options
    assert '--ask-pass' in p.options


def test_localhost(p):
    p.parse(['init', '@localhost'])
    assert '-c' in p.options
    assert 'local' in p.options
    assert p.options.index('local') == p.options.index('-c') + 1


def test_ssh_config(p):
    p.parse(['init', '@host'])
    assert '--ssh-extra-args' in p.options


def test_vars(p):
    p.parse([
        'init', '--extra=opt',
        'extra-opt2',
        'extra=var'
    ])
    assert 'extra-opt2' in p.options
    assert '--extra=opt' in p.options
    assert p.options[p.options.index('--extra=opt') - 1] != '-e'
    assert 'extra=var' in p.options
    assert p.options[p.options.index('extra=var') - 1] == '-e'


def test_subvars(p):
    p.parse(['init', 'env.testsub=value'])
    assert '-e' in p.options
    assert json.dumps({'env': {'testsub': 'value'}}) in p.options


def test_deep_vars(p):
    p.parse(['init', 'test.very.deep.var=deep'])
    assert json.dumps({
        'test': {
            'very': {
                'deep': {'var': 'deep'}
            }}}) in p.options


def test_merge_vars(p):
    p.parse(['init', 'test.sub=value1', 'test.sub2=value2'])
    assert json.dumps({
        'test': {
            'sub': 'value1',
            'sub2': 'value2'
        }
    }) in p.options


def test_role_uniq(p):
    p.parse(['install', 'rolename'])
    assert 'rolename' in p.roles


def test_role_multi(p):
    roles = 'nginx,docker,firewall'
    p.parse(['install', roles])
    assert p.roles == roles.split(',')


def test_plugin_uniq(p):
    p.parse(['init', '-p', 'django'])
    assert 'plugins=django' in p.options


def test_plugin_multi(p):
    plugins = 'django,postgres,sentry'
    p.parse(['init', '-p', plugins])
    assert f'plugins={plugins}' in p.options
    assert p.options[p.options.index(f'plugins={plugins}') - 1] == '-e'


def test_inventory_uniq(p):
    dirpath = os.path.join(os.path.dirname(__file__), '..')
    invpath = os.path.join(dirpath, 'inventory_template/inventory.yaml')
    p.parse(['init', '-i', invpath])
    assert invpath in p.options
    assert p.options[p.options.index(invpath) - 1] == '-i'


def test_inventory_multi(p):
    dirpath = os.path.join(os.path.dirname(__file__), '..')
    invpath1 = os.path.join(dirpath, 'inventory_template/inventory.yaml')
    invpath2 = os.path.join(dirpath, 'init.yml')
    p.parse(['init', '-i', ','.join([invpath1, invpath2])])
    assert invpath1 in p.options
    assert p.options[p.options.index(invpath1) - 1] == '-i'
    assert invpath2 in p.options
    assert p.options[p.options.index(invpath2) - 1] == '-i'
