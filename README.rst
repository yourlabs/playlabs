Playlabs: the obscene ansible distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DISCLAMER: maybe it even works for you, but that's far from garanteed so far.

I love ansible most of the time, the rest of the time it makes me feel like
it deserves better UX. Playlabs unfrustrates me:

- provides a CLI to generate ansible-playbook commands,
- works without inventory with options passed on the CLI,
- also works with an inventory, that it standardizes,
- able to combine both of the above,
- provides a generic "project" role for my custom projects CD, that provides
  with nginx-proxy, letsencrypt-companion, netdata monitoring, sentry, etc
- 1-click galaxy role install, role sub-task execution, chaining, etc, using
  generic playbooks
- provides a command to setup ansible host dependencies (enforcing python3), my
  user with my key and passwordless sudo and disable root and password ssh
  access (my way or the highway !)
- also supports k8s, but I won't prescribe it until you need HA

A more extensive and user-friendly documentation is in the docs sub-directory
of playlabs and online @ https://playlabs.rtfd.io thanks to RTFD :)

Install playlabs
================

This would install in the ~/src/playlabs directory::

    pip3 install --user --editable git+https://yourlabs.io/oss/playlabs#egg=playlabs

Run the ansible-playbook wrapper command without argument to see the quick
getting started commands::

    ~/.local/bin/playlabs
    # or:
    echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc

Then, install your user with your public key, passwordless sudo, and secure SSH
for the playlabs install command to work. Playlabs provide two ways.

Vagrant/VirtualBox
------------------

You can work in a VM if you have vagrant::

   cd ~/src/playlabs
   vagrant destroy -f
   vagrant up
   vagrant ssh-config > ssh
   playlabs deploy image=yourlabs/crudlfap --ssh-common-args="-F ssh" @default

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

Deploy a project
================

Without inventory
-----------------

You can now deploy a container for a custom image, it will create a
``project-staging`` container by default::

    playlabs @192.168.168.168 deploy image=betagouv/mrs:master

This time with more variables and in ``ybs-hack`` instead of
``project-staging``::

    playlabs @192.168.168.168 deploy
        image=betagouv/mrs:master
        prefix=ybs
        instance=hack
        plugins=postgres,django,uwsgi
        backup_password=foo
        env.SECRET_KEY=itsnotasecret
        env.VIRTUAL_HOST=ybs.hack.example.com
        env.LETSENCRYPT_HOST=ybs.hack.example.com
        env.LETSENCRYPT_EMAIL=your@example.com

With inventory
--------------

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

Installing roles
================

You will probably want to monitor your server::

   playlabs install netdata @192.168.168.168

You could also install galaxy roles that contain a dot, in which case playlabs
will automatically download it if necessary::

   playlabs install ferrarimarco.virtualbox @192.168.168.168

You could also execute a specific role task file instead of main.yml, if your
role name contains a slash::

   # run k8s/tasks/users.yml instead of k8s/tasks/main.yml
   # in the CI of your inventory for example to react to changes ?
   playlabs install k8s/users @192.168.168.168

Note that the dot and slash notations should be compatible.

You can also execute multiple roles at once if you separate them by comma::

   playlabs install netdata,ferrarimarco.virtualbox,k8s/users @192.168.168.168

You can set ansible variables directly on the command line. If you use dot in
variable name, it will build a dict, ie.::

   playlabs install netdata @192.168.168.168 example=lol foo.bar=test
   # will generate the extra ansible-playbook options:
   ansible-playbook ... -e example=lol -e '{"foo": {"bar": "test"}}'

Kubernetes
==========

We also have k8s support, but beware that it's not compatible with the deploy
command, that relies on nginx-proxy and its letsencrypt companion, it's
currently in-development and not tested in production, but still pretty cool::

   playlabs install k8s @192.168.168.168

   # run k8s/tasks/init.yml instead of k8s/tasks/main.yml to reset a cluster
   playlabs install k8s/init @192.168.168.168

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
