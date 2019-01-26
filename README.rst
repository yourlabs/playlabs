Playlabs: the obscene ansible distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Playlabs combines simple ansible patterns with packaged roles to create a
docker orchestrated paas to prototype products for development to production.

Playlabs does not deal with HA, for HA you will need to do the ansible plugins
yourself, or use kubernetes ... but Playlabs will do everything else, even
configure your own sentry or kubernetes servers !

DISCLAMER: maybe it even works for you, but that's far from garanteed so far.

Install playlabs
================

This would install in the ~/src/playlabs directory::

    pip3 install --user --editable git+https://yourlabs.io/oss/playlabs#egg=playlabs

Run the ansible-playbook wrapper command without argument to see the quick
getting started commands::

    ~/.local/bin/playlabs

Vagrant
=======

In the git directory of playlabs, you can run ``vagrant up`` to have a VM on
192.168.168.168 that you can ssh to with sudo access (it has been "initialized"
by playlabs, see next section for detail about playlabs initialization)::

   cd ~/src/playlabs
   vagrant destroy -f
   vagrant up
   playlabs install docker,k8s @192.168.168.168

Quick start
===========

You have a new host and you need your user to be installed with your public
key, passwordless sudo, and secure SSH. The first command to run on a new host
is ``playlabs init``, ie.::

    playlabs init root@1.2.3.4

    # all options are ansible options are proxied
    playlabs init @192.168.168.168 --ask-become-pass

    # example with a typical openstack vm
    playlabs init ubuntu@192.168.168.168 --ask-become-pass

Now your user can install roles::

    # nginx-proxy based infra
    playlabs install ssh,docker,firewall,nginx @192.168.168.168

    # k8s based infra
    playlabs install ssh,docker,k8s @192.168.168.168

    # run k8s/tasks/users.yml instead of k8s/tasks/main.yml
    playlabs install k8s/users @192.168.168.168

And deploy a project, examples::

    playlabs @192.168.168.168 deploy image=betagouv/mrs:master
    playlabs @192.168.168.168 deploy
        image=betagouv/mrs:master
        plugins=postgres,django,uwsgi
        backup_password=foo
        prefix=ybs
        instance=hack
        env.SECRET_KEY=itsnotasecret
    playlabs @192.168.168.168 deploy
        prefix=testenv
        instance=$CI_BRANCH
        image=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

If you have that work, creating an inventory is the way to move on, wether you
want to version configuration, add a deploy user for your CI, configure a
secret backup password, add ssh-keys ...::

    playlabs scaffold ./your-inventory

Read on this README for gory details if you are already an Ansible user and
only need to know about the patterns we're using playlabs for.

A more extensive and user-friendly documentation is in the docs sub-directory
of playlabs and online @ https://playlabs.rtfd.io thanks to RTFD :)

``playlabs init``
=================

Initializing means going from a naked system to a system with your own user,
ssh key, dotfiles, sudo access, secure sshd, and all necessary dependencies to
execute ansible, such as python3. It will also install your friend account if
you have an ansible inventory repository where you store your friend list in
yml.

You might need to pass extra options to ansible in some cases, for example if
your install provides a passworded sudo, add ``--ask-sudo-pass`` or put the
password in the CLI, since initializing will remove ::

    playlabs init @192.168.168.168
    playlabs init user:pass@192.168.168.168
    playlabs init user@192.168.168.168 --ask-sudo-pass
    playlabs init root@192.168.168.168

``playlabs install``
====================

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

    playlabs install docker,firewall,nginx @192.168.168.168 # the paas for the project role
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
