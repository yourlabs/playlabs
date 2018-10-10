Playlabs: the obscene ansible distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Playlabs combines simple ansible patterns with packaged roles to create a
docker orchestrated paas to prototype products for development to production.

Playlabs does not deal with HA, for HA you will need to do the ansible plugins
yourself, or use kubernetes ... but Playlabs will do everything else, even
configure your own sentry or kubernetes servers !

DISCLAMER: maybe it even works for you, but that's far from garanteed so far.

Quick start
===========

Init your ssh user with your key and secure sshd and passwordless sudo:

    playlabs init root@1.2.3.4
    # all options are ansible options are proxied
    playlabs init @somehost --ask-become-pass

Now your user can install roles:

    playlabs install ssh,docker,firewall,nginx @somehost

And deploy a project, examples:

    playlabs @somehost deploy image=betagouv/mrs:master
    playlabs @somehost deploy
        image=betagouv/mrs:master
        plugins=postgres,django,uwsgi
        backup_password=foo
        prefix=ybs
        instance=hack
        env.SECRET_KEY=itsnotasecret
    playlabs @somehost deploy
        prefix=testenv
        instance=$CI_BRANCH
        image=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

If you have that work, creating an inventory is the way to move on, wether you
want to version configuration, add a deploy user for your CI, configure a
secret backup password, add ssh-keys ...:

    playlabs scaffold ./your-inventory

Install playlabs
================

Install with::

    pip3 install --user -e git+https://yourlabs.io/oss/playlabs#egg=playlabs

Run the ansible-playbook wrapper command without argument to see the quick
getting started commands::

    ~/.local/bin/playlabs

Read the following for more gory details.

0. Init
=======

Initializing means going from a naked system to a system with your own user,
ssh key, dotfiles, sudo access, secure sshd, and all necessary dependencies to
execute ansible, such as python3. It will also install your friend account if
you have an ansible inventory repository where you store your friend list in
yml.

You might need to pass extra options to ansible in some cases, for example if
your install provides a passworded sudo, add ``--ask-sudo-pass`` or put the
password in the CLI, since initializing will remove ::

    playlabs init @somehost
    playlabs init user:pass@somehost
    playlabs init user@somehost --ask-sudo-pass
    playlabs init root@somehost

1. Roles
========

If you want to deploy your project, then you need to install the paas which
consists of three roles: docker, firewall, and nginx. The nginx role sets up
two containers, nginx-proxy that watches the docker socket and introspects
docker container environment variables, such as VIRTUAL_HOST, to reconfigure
itself, it even supports uWSGI. The other container is nginx-letsencrypt, that
shares a cert volume with the nginx-proxy container, and watches the docker
socket for containers and introspect variables such as LETSENCRYPT_EMAIL, to
configure the certificates.

Remember the architecture:

- nginx-proxy container recieves requests,
- nginx-letsencrypt container generates certificates,
- other docker containers have environment variables necessary for the above

The CLI itself is pretty straightforward::

    playlabs install docker,firewall,nginx @somehost # the paas for the project role
    playbabs install sendmail,netdata,mailcatcher,gitlab @staging
    playbabs install sendmail,netdata,sentry user@production

The difference between traditionnal roles and playlabs roles, is that in
playlabs they strive to have stuff running inside docker to leverage the
architecture of the nginx proxy.

Playlabs can configure sendmail of course, but also has roles providing
full-featured docker based mailservers or mailcatcher instances for your dev,
training or staging environments for example.

This approach comes from migrating away from "building in production" to
"building immutable tested chroots", away from "pet" to "cattle".

But if you're already an ansible hacker you're better off with ansible to do a
**lot** more than than what docker-compose has to offer, such as managing users
and roles, on your SDN as in your apps.

In fact, you will see role that consist of a single docker ansible module call,
but the thing is that you can spawn it in one command and have it integrated
with the rest of your server, and even rely on ansible to provision
fine-grained RBAC in your own apps.

2. Project: deployments
=======================

The `project` role is made to be generic and cover infrastructure needs to
develop a project, from development to production. Spawn an environment, here
with an example image this repo is tested against::

    playlabs @yourhost deploy betagouv/mrs:master '{"env":{"SECRET_KEY" :"itsnotasecret"}}'

It will use the IP address by default if ansible finds it, set the dns with the
dns option ``dns=yourdns.com``, or set it in ``project_staging_dns`` yaml
variable of `your-inventory/group_vars/all/project.yml`.

This is because the default prefix is ``project`` and the default instance is
``staging``. Let's learn a new way of specifiying variables, add to your
variables::

    yourproject_production_image: yourimage:production
    yourproject_production_env:
      SECRET_KEY: itsnotsecret
      # the above value could be encrypted with ansible-vault s_encrypt

Then you can deploy as such::

    playlabs @yourhost deploy prefix=yourproject instance=production

If you configure yourhost in your inventory, in group "yourproject-production",
then you don't have to specify the host anymore::

    playlabs @yourhost project prefix=$CI_PROJECT instance=$CI_BRANCH

3. Project: plugins
===================

PostgreSQL or Django or uWSGI support are provided through project plugins,
which you may activate as such:

- specify ``-p postgres,uwsgi,django``
- configure ``yourprefix_yourinstance_plugins=[postgres, uwsgi, django]``
- add to Dockerfile ``ENV PLAYLABS_PLUGINS postgres,uwsgi,django``

The order of plugins matters, having postgres first ensures postgres is started
before the project image.

Plugins are directories located at the root of playlabs repo, but at some point
we can imagine loading them from the image itself.

Plugins contain the following:

- vars.yml: variables that are auto-loaded
- deploy.pre.yml: tasks to execute before deploy of the project image
- deploy.post.yml: tasks to execute after deploy of the project image
- backup.pre.sh: included in backup.sh template before the backup
- backup.post.sh: included in backup.sh template before the backup
- restore.pre.sh: included in restore.sh template before the restore
- restore.post.sh: included in restore.sh template before the restore

5. Inventory (git versioning of cfg)
====================================

Most roles require an inventory to be really fun. Initiate an empty repository
where you will store your data that the roles should use::

    playlabs scaffold your-inventory

In inventory.yml you can define your machines as well as the roles they should
be included by default in when playing a role without a specific target::

    all:
      hosts:
        yourhost.com:
        otherhost:
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
        hosts: [yourhost.com, otherhost]

You can add as much metadata as you want in group_vars, for now let's add some
users to ``your-inventory/group_vars/all/users.yml``::

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

Every time you init a machine from a directory that is an inventory, it
will install all users.

Options
=======

Ansible
-------

Some of the variables you can like ::

    -e key=value                    # set variable "key" to "value"
    -e '{"key":"value"}'            # same in json
    -i path/to/inventory_script.ext # load any numbers of inventory variables
    -i 1.2.4.4,                     # add a host by ip to this play
    --limit 1.2.4.4,                # limit play execution to these hosts
    --user your-other-user          # specify a particular username
    --noroot                        # don't try becoming root automatically

Global variables
----------------

Variables that are used by convention accross roles::

    letsencrypt_uri=https...
    letsencrypt_email=your@...

Role variables
--------------

Base variable are defined in `playlabs/roles/rolename/vars/main.yml` and start
with the `rolename_`, they can be overridden in your inventory's
`group_vars/all/rolename.yml`.

The base variable will default to the same variable without the `rolename_`
prefix::

    # Set project_image project role variable from the command line
    image=your/image:tag

Role structure
--------------

Default roles live in playlabs/roles and share the `standard directory
structure with ansible roles
<https://docs.ansible.com/ansible/2.5/user_guide/playbooks_reuse_roles.html>`_,
that you can scaffold with the ansible-galaxy tool.

Playlabs use roles as alternatives as docker-compose when possible, rather than
polluting the host with many services.

Project variables
-----------------

The project role base variables calculate to be overridable by prefix/instance::

    # project_{image,*} base value references project_staging_{image,*} from inventory
    instance=staging

    # project_{image,*} base value references mrs_production_{image,*} from inventory
    instance=production prefix=mrs

Project plugins variable
------------------------

The project role has a special plugins variable that can be overridden in the
usual way, but it will also try to find it by introspecting the docker image
for the `PLAYLABS_PLUGINS` env var ie::

    ENV PLAYLABS_PLUGINS postgres,django,uwsgi,sentry

Plugin variables
----------------

Plugin variables are loaded by the project role for each plugin that it loads
if any.

Base plugin variables start with `project_pluginname_` and the special
`project_pluginname_env` variable should be a dict, they will be all merged to
add environment variables to the project container, project_env will be a merge
of all them plugin envs.

Plugin env vars should preferably use overridable variables.

Plugin structure
----------------

Default plugins live in playlabs/plugins and have the following files:

- `backup.pre.sh` take files out of containers and add them to the $backup
  `variable
- `backup.post.sh` clean up files you have taken out after the backup has been
  `done
- `restore.pre.sh` clear the place where you want to extract data from the
  `restic backup repository
- `restore.post.sh` load new data and clean after the project was restarted in
  `the snapshot version,
- `deploy.pre.yml` ansible tasks to execute before project deployment, ie. spawn
  `postgres
- `deploy.post.yml` ansible tasks to execute after project deployment, ie.
  `create users from inventory
- `vars.yml` plugin variables declaration

Operations
==========

By default, it happens in /home/yourprefix-yourinstance. Contents depend on the
activated plugins.

In the /home/ directory of the role or project there are scripts:

- `docker-run.sh` standalone command to start the project container, feel free
  `to have on that one
- `backup.sh` cause a secure backup, upload with lftp if inventory defines dsn
- `restore.sh` recovers the secure backup repository
  `with lftp if inventory desfines dsn. Without argument` list snapshots. With a
  `snapshot argument` proceed to a restore of that snapshot including project
  `image version and plugin data
- `prune.sh` removes un-needed old backup snapshots
- `log` logs that playlabs rotates for you, just fill in log files, it will do
  a copy truncate though, but works until you need prometheus or something

For backups to enable, you need to set backup_password, either with -e, either
through yourpefix_yourinstance_backup_password.

The restic repository is encrypted, if you set the lftp_dsn or
yourprefix_yourinstance_lftp_dsn then it will use lftp to mirror them. If you
trash the local restic repository, and run restore.sh, then it will fetch the
repository with lftp.
