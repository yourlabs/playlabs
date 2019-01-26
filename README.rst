Playlabs: the obscene ansible distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Playlabs combines simple ansible patterns with packaged roles to create a
docker orchestrated paas to prototype products for development to production.

Playlabs does not deal with HA, for HA you will need to do the ansible plugins
yourself, or use kubernetes ... but Playlabs will do everything else, even
configure your own sentry or kubernetes servers !

DISCLAMER: maybe it even works for you, but that's far from garanteed so far.
Most tasks have been put inside this repository without prior testing with the
playlabs command or the playlabs inventory. I like to keep them there so I have
them when I need them I fix them, those that are fixed work for me.

A more extensive and user-friendly documentation is in the docs sub-directory
of playlabs and online @ https://playlabs.rtfd.io thanks to RTFD :)

Install playlabs
================

This would install in the ~/src/playlabs directory::

    pip3 install --user --editable git+https://yourlabs.io/oss/playlabs#egg=playlabs

Run the ansible-playbook wrapper command without argument to see the quick
getting started commands::

    ~/.local/bin/playlabs

Then, install your user with your public key, passwordless sudo, and secure SSH
for the playlabs install command to work. Playlabs provide two ways.

Vagrant/VirtualBox
------------------

In the git directory of playlabs, you can run ``vagrant up`` to have a VM on
192.168.168.168 that you can ssh to with sudo access::

   cd ~/src/playlabs
   vagrant destroy -f
   vagrant up
   ssh 192.168.168.168 date
   playlabs install docker,k8s @192.168.168.168

Bare host
---------

The ``playlabs init`` command can setup your user for you::

    # example with root acces
    playlabs init root:aoeu@1.2.3.4

    # all options are ansible options are proxied
    playlabs init @192.168.168.168 --ask-become-pass

    # example with a typical openstack vm
    playlabs init ubuntu@192.168.168.168 --ask-become-pass

Now you should be able to install roles.

Installing roles
================

If you're going to use playlabs to deploy docker images, you have the choice
between the nginx-proxy infra::

   # nginx-proxy based infra
   playlabs install ssh,docker,firewall,nginx @192.168.168.168

And the k8s-based infra::

   # k8s based infra
   playlabs install ssh,docker,k8s @192.168.168.168

As you might have noticed, playlabs prints out the ansible-playbook command
line it bakes. This allows for many obscenities such as this little shortcut::

   # run k8s/tasks/init.yml instead of k8s/tasks/main.yml to reset a cluster
   playlabs install k8s/init @192.168.168.168

   # run k8s/tasks/users.yml in the CI of your inventory for example
   playlabs install k8s/users @192.168.168.168

Deploy a project with the nginx-proxy based infra
=================================================

Deploying an image on the host ip in container ``project-staging``::

    playlabs @192.168.168.168 deploy image=betagouv/mrs:master

This time with more variables and in ``ybs-hack`` instead of
``project-staging``::

    playlabs @192.168.168.168 deploy
        image=betagouv/mrs:master
        plugins=postgres,django,uwsgi
        backup_password=foo
        prefix=ybs
        instance=hack
        env.SECRET_KEY=itsnotasecret

To generate a starter inventory where you can store variables such as users,
keys, passwords with ansible-vault, etc::

    playlabs scaffold ./your-inventory

Then from CI of a project, you can auto-deploy the ybs-hack instance from above
as such (it will pickup the ``ybs_hack_*`` variables from the inventory)::

    playlabs @192.168.168.168 deploy
        prefix=ybs
        instance=hack
        instance=$CI_BRANCH
        image=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

Command explanation
===================

``playlabs init``
-----------------

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
--------------------

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
**lot** more than than what docker-compose has to offer, such as managing k
and roles, on your SDN as in your apps.

In fact, you will see role that consist of a single docker ansible module call,
but the thing is that you can spawn it in one command and have it integrated
with the rest of your server, and even rely on ansible to provision
fine-grained RBAC in your own apps.
