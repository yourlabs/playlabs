Projects deployments and lifecycles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

WIP doc

Pre-requisite
=============

You need a sudo access on the remote machine, which can typically be obtained
with the ``playlabs init`` command ie.::

    playlabs init root@1.2.3.4

    # all options are ansible options are proxied, so this also works
    playlabs init @somehost --ask-become-pass

The ssh, docker and firewall playlabs roles must be installed on the server::

    playlabs install ssh,docker,firewall,nginx @somehost

Deploying a docker image
========================

Examples::

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

Deployments
===========

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

Project plugins
===============

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

Default plugins live in playlabs/plugins and have the following files:

- `backup.pre.sh` take files out of containers and add them to the $backup
  variable
- `backup.post.sh` clean up files you have taken out after the backup has been
  done
- `restore.pre.sh` clear the place where you want to extract data from the
  restic backup repository
- `restore.post.sh` load new data and clean after the project was restarted in
  the snapshot version,
- `deploy.pre.yml` ansible tasks to execute before project deployment, ie. spawn
  postgres
- `deploy.post.yml` ansible tasks to execute after project deployment, ie.
  create users from inventory
- `vars.yml` plugin variables declaration

Operations
==========

By default, it happens in /home/yourprefix-yourinstance. Contents depend on the
activated plugins.

In the /home/ directory of the role or project there are scripts:

- `docker-run.sh` standalone command to start the project container, feel free
  to have on that one
- `backup.sh` cause a secure backup, upload with lftp if inventory defines dsn
- `restore.sh` recovers the secure backup repository
  with lftp if inventory desfines dsn. Without argument` list snapshots. With a
  snapshot argument` proceed to a restore of that snapshot including project
  image version and plugin data
- `prune.sh` removes un-needed old backup snapshots
- `log` logs that playlabs rotates for you, just fill in log files, it will do
  a copy truncate though, but works until you need prometheus or something

For backups to enable, you need to set backup_password, either with -e, either
through yourpefix_yourinstance_backup_password.

The restic repository is encrypted, if you set the lftp_dsn or
yourprefix_yourinstance_lftp_dsn then it will use lftp to mirror them. If you
trash the local restic repository, and run restore.sh, then it will fetch the
repository with lftp.
