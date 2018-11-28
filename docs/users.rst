User and groups management
~~~~~~~~~~~~~~~~~~~~~~~~~~

The main feature of playlabs is your inventory, it's meant to make it easy for
you to manage users and users to manage themselves on your infra & external
services. For example, playlabs could provision ssh and ldap on an ldap server,
but so far we haven't provisioned ldap servers with playlabs because we have
playlabs ... wait wut ?

Anyway, when you're onboarding a hacker you can point them to your inventory
repository url and also this documentation with the mission to add themselve.

Adding a new users
==================

Clone the playlabs inventory repository. If it doesn't work, make sure that the
git server knows your ssh public key if authenticating with SSH.

The users list and roles are defined in a YAML document that would be located
in your repository at path ``group_vars/all/users.yml``. Ansible offers a wide
range of possibilities so it might also be elsewhere, but that's the convention
used in the default playlabs inventory that you can generate with the
``playlabs scaffold`` command.

The users YAML document in the default repository serves as reference:

.. literalinclude:: ../playlabs/inventory_template/group_vars/all/users.yml
