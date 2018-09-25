Playlabs: the obscene ansible distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Playlabs combines simple ansible patterns with packaged roles to create a
docker orchestrated paas to prototype products for development to production.

Playlabs does not deal with HA, for HA you will need to do the ansible plugins
yourself, or use kubernetes ... but Playlabs will do everything else, even
configure your own sentry or kubernetes servers !

Install playlabs
================

Use the docker image or install with: pip3 install --user playlabs

Run the ansible-playbook wrapper command: ~/.local/bin/playlabs

It will prompt if you want to add ~/.local/bin to your ~/.bash_profile, if you
accept it will setup your shell so that you can call just ``playlabs`` directly
in future logins.

0. Bootstrap
============

"Boostrap" means installng your own user with your ssh key, sudo access and all
necessary dependencies to execute ansible, and then installing all your friends
account if you have already done the next step and have an inventory :D

When playlabs command detects that the first argument has an @ then it will
attempt to bootstrap the host.

Note that playlabs will pass any extra argument to the underneath
ansible-playbook call.

Run::

    playlabs root@somehost
    playlabs @somehost          # will use sudo as your user

That will execute the bootstrap.yml playbook, which in turn will execute
bootstrap.sh on the server with Ansible's script module that doesn't require
python.

You might need to pass extra options to ansible in some cases, for example if
your install provides a passworded sudo, add ``--ask-sudo-pass``.

You can then for example reboot the server::

    playlabs reboot @somehost  # requires ansible 1.7
    # the reboot role's task/main.yml has a comment playlabs user=root
    # so playlabs know it has to escalade to apply this role

Proceed on to deploying some roles there !

1. Roles
========

The difference between traditionnal roles and playlabs roles, is that in
playlabs they strive to have stuff running inside docker and being nginx-proxy
which has automatic letsencrypt. Playlabs can configure sendmail of course, but
also has roles providing full-featured docker based mailservers or mailcatcher
(for your training or staging environments for example). This approach comes
from excessive frustration over docker-compose, that if you're already an
ansible hacker you're better off with ansible to do a **lot** more than just
spawning containers in an unpredictible order (that's how compose was in the
days for me). In fact, you will see role that consist of a single docker
ansible module call, but the thing is that you can spawn it in one command and
have it integrated with the rest of your server, and even rely on ansible to
provision fine-grained RBAC in your own apps::

    playlabs @somehost paas   # equivalent to docker,firewall,nginx
    playbabs @staging sendmail,netdata,mailcatcher,gitlab
    playbabs @production sendmail,netdata,sentry

2. Inventory
============

Most roles require an inventory to be really fun. Initiate an empty repository
where you will store your data that the roles should use::

    playlabs init your-inventory

In inventory.yml you can define your machines as well as the roles they should
be included by default in when playing a role without a specific target.

    all:
      hosts:
        yourhost:
          fqdn: yourdomain.tld
          ansible_ssh_port: 22
          ansible_ssh_host: 123.12.12.23

    children:
      netdata:
        hosts:
          yourhost

In the above you have created a netdata group with a host yourhost. Executing
the netdata role without explicit @ target will automacitally install netdata
on yourhost thanks to that.

Given how free ansible limit syntax lets us, we can use rich notations such as
this one to add two hosts to two roles at once::

    children:
      netdata-mailcatcher:
        hosts: [yourhost0, yourhost1]

You can add as much metadata as you want in group_vars, for now let's add some
users to group_vars/all/users.yml::

    ---
    users:
    - name: jl
      first_name: John  # used by django role for example
      email: aoeu@example.com
      key: 'ssh-...'
      roles:
        ssh: sudo
        k8s: cluster-admin
        sentry: superuser

Be carefull that roles for a user are a 2d matrix: each key or value may
correspond to an ansible role name, the other is the level of user within that
role, that's why roles is a key value pair.

Every time you bootstrap a machine from a directory that is an inventory, it
will install all users.

3. Project: deployment
======================

The project role is made to be generic and cover infrastructure needs to
develop a project, from development to production. Spawn an environment, here
with an example image this repo is tested against::

    playlabs @yourhost project  -e image=betagouv/mrs:master -e plugins=django -e backup_password=foo -e '{"env":{"SECRET_KEY" :"itsnotasecret"}}'

If your project name is yourproject, you can setup the staging environment as
such in your-inventory/group_vars/all/yourproject-secrets.yml (use
ansible-vault if you want)::

    # apply to staging
    yourproject_staging_backup_password: aotsnesaotnehustoaheuooseutasoeut

    # apply to yourproject
    yourproject_plugins: [django,uwsgi,postgres,sentry]

4. Project: operations
======================

backup
restore
logs
