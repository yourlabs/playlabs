Playlabs: the obscene ansible distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Playlabs combines simple ansible patterns with packaged roles to create a
docker orchestrated paas to prototype products for development to production.

Playlabs does not deal with HA, for HA you will need to do the ansible plugins
yourself, or use kubernetes ... but Playlabs will do everything else, even
configure your own sentry or kubernetes servers !

Install playlabs
================

Install with:: 

    pip3 install --user -e git+https://yourlabs.io/oss/playlabs#egg=playlabs

Run the ansible-playbook wrapper command:: 

    ~/.local/bin/playlabs

`playlabs` CLI overview
=======================

Overview of CLI commands:

- Bootstrap deploys your user, prepares for role deployment
- Role deployment for project is: docker,firewall,nginx
- Project deployment includes plugins is settable by `prefix_instance_` variables
- Initiate a repository from the example repository folder

Clumsily converts `you@host` to `--user=you --limit=host --inventory host,`,
Adds `--inventory inventory.yml` if it finds an inventory yaml in the current
working directory,
Proxies other variables to ansible, such as `-e`/`--extra-var`.
Has many bugs.

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

    playlabs @somehost docker,firewall,nginx  # the paas for the project role
    playbabs @staging sendmail,netdata,mailcatcher,gitlab
    playbabs @production sendmail,netdata,sentry

2. Project: deployments
=======================

The project role is made to be generic and cover infrastructure needs to
develop a project, from development to production. Spawn an environment, here
with an example image this repo is tested against::

    playlabs @yourhost project -e image=betagouv/mrs:master -e '{"env":{"SECRET_KEY" :"itsnotasecret"}}'

It will use the IP address by default, but you can pass a dns with ``-e
dns=yourdns.com``, or set it in ``project_staging_dns`` yaml variable of
your-inventory/group_vars/all/project.yml

This is because the default prefix is ``project`` and the default instance is
``staging``. Let's learn a new way of specifiying variables, add to your
variables::

    yourproject_production_image: yourimage:production
    yourproject_production_env:
      SECRET_KEY: itsnotsecret

Then you can deploy as such::

    playlabs @yourhost project @host -e prefix=yourproject -e instance=production

If you configure yourhost in your inventory, in group "yourproject-production",
then you don't have to specify the host anymore::

    playlabs @yourhost project -e prefix=yourproject -e instance=production

Note that you can also use ansible-vault'ed files or variables, refer to
Ansible documentation for that.

3. Project: plugins
===================

You can add plugins to your project in several ways, suppose you want to add
two plugins:

- specify ``-e plugins=django,postgres``
- configure ``yourprefix_yourinstance_plugins=[django, postgres]``
- add to Dockerfile ``ENV PLAYLABS_PLUGINS django,postgres``

Plugins are directories located at the root of playlabs repo, but at some point
might be git repo urls ...

They have the following files:

- vars.yml: variables that are auto-loaded
- deploy.pre.yml: tasks to execute before deploy of the project image
- deploy.post.yml: tasks to execute after deploy of the project image
- backup.pre.sh: inserted in backup.sh before the backup
- backup.post.sh: inserted in backup.sh before the backup
- restore.pre.sh: inserted in restore.sh before the restore
- restore.post.sh: inserted in restore.sh before the restore

5. Inventory (git versioning of cfg)
====================================

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

Options
=======

Ansible
-------

    -e key=value 			# set variable "key" to "value"
    -e '{"key":"value"}' 		# same in json
    -i path/to/inventory_script.ext 	# load any numbers of inventory variables
    -i 1.2.4.4,				# add a host by ip to this play
    --limit 1.2.4.4,			# limit play execution to these hosts
    --user your-other-user 		# specify a particular username
    --noroot 				# don't try becoming root automatically

Global variables
----------------

Variables that are used by convention accross roles:

    -e letsencrypt_uri=https...
    -e letsencrypt_email=your@...

Role variables
--------------

Base variable are defined in playlabs/roles/rolename/vars/main.yml and start
with the `rolename_`, they can be overridden in your inventory's
`group_vars/all/rolename.yml`.

The base variable will default to the same variable without the `rolename_`
prefix:

    # Set project_image project role variable from the command line
    -e image=your/image:tag 

Role structure
--------------

Default roles live in playlabs/roles and share the
[standard directory structure with ansible roles](https://docs.ansible.com/ansible/2.5/user_guide/playbooks_reuse_roles.html),
that you can scaffold with the ansible-galaxy tool.

Playlabs use roles as alternatives as docker-compose
when possible, rather than polluting the host with
many services.

Project variables
-----------------

The project role base variables calculate to be overridable by prefix/instance:

    # project_{image,*} base value references project_staging_{image,*} from inventory
    -e instance=staging  

    # project_{image,*} base value references mrs_production_{image,*} from inventory
    -e instance=production -e prefix=mrs

Project plugins variable
------------------------

The project role has a special plugins variable that can be overridden in the
usual way, but it will also try to find it by introspecting the docker image
for the `PLAYLABS_PLUGINS` env var ie::

    ENV PLAYLABS_PLUGINS postgres,django,uwsgi,sentry

Plugin variables
----------------

Plugin variables are loaded by the project role for
each plugin that it loads if any.

Base plugin variables start with
`project_pluginname_` and the special
`project_pluginname_env` variable should be a dict,
they will be all merged to add environment variables
to the project container, project_env will be a
merge of all them plugin envs.

Plugin env vars should preferably use overridable variabls.

Plugin structure
----------------

Default plugins live in playlabs/plugins and have
the following files:

- backup.pre.sh: take files out of containers and add them to the $backup variable
- backup.post.sh: clean up files you have taken out
  after the backup has been done
- restore.pre.sh: clear the place where you want to
  extract data from the restic backup repository
- restore.post.sh: load new data and clean after the
  project was restarted in the snapshot version, 
- deploy.pre.yml: ansible tasks to execute before
  project deployment, ie. spawn postgres
- deploy.post.yml: ansible tasks to execute after
  project deployment, ie. create users from
inventory
- vars.yml: plugin variables declaration

Appendix
https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html

Operations
==========

By default, it happens in /home/yourprefix-yourinstance. Contents depend on the
activated plugins.

In the /home/ directory of the role or project there are scripts:

- docker-run.sh: standalone command to start the
  project container, feel free to have on that one
- backup.sh: cause a secure backup, upload with lftp
  if inventory defines dsn
- restore.sh: recovers the secure backup repository
  with lftp if inventory desfines dsn. Without
argument: list snapshots. With a snapshot argument:
proceed to a restore of that snapshot including
project image version and plugin data 
- prune.sh: removes un-needed old backup snapshots
- log: logs that playlabs rotates for you, just stack em in

For backups to enable, you need to set backup_password, either with -e, either
through yourpefix_yourinstance_backup_password.

The restic repository is encrypted, if you set the lftp_dsn or
yourprefix_yourinstance_lftp_dsn then it will use lftp to mirror them. If you
trash the local restic repository, and run restore.sh, then it will fetch the
repository with lftp.
