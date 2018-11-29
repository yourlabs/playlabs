User and groups management
~~~~~~~~~~~~~~~~~~~~~~~~~~

The main feature of playlabs is your inventory, it's meant to make it easy for
you to manage users and users to manage themselves on your infra & external
services. For example, playlabs could provision ssh and ldap on an ldap server,
but so far we haven't provisioned ldap servers with playlabs because we have
playlabs ... wait wut ?

Anyway, when you're onboarding a hacker you can point them to your inventory
repository url and also this documentation with the mission to add themselve.

Adding a new user
=================

Clone the playlabs inventory repository. If it doesn't work, make sure that the
git server knows your ssh public key if authenticating with SSH.

The users list and roles are defined in a YAML document that would be located
in your repository at path ``group_vars/all/users.yml``. Ansible offers a wide
range of possibilities so it might also be elsewhere, but that's the convention
used in the default playlabs inventory that you can generate with the
``playlabs scaffold`` command.

Secret variables
----------------

Create a password for yourself::

    echo -n your password | ansible-vault encrypt --vault-id .vault > passwords/$USER

SSH will not accept password authentication with playlabs by default, however
your password will be useable with the rest of services installed with
playlabs, even custom projects if their plugin support it, which is the case of
the Django plugin, thanks to `djcli <https://yourlabs.io/oss/djcli>`_.

SSH Public key
--------------

Playlabs will use the SSH key it finds in the ``keys/`` inventory of the
inventory repository. You can set it up as such::

    # generate a key if you don't have any
    ssh-keygen -t ed25519 -a 100

    # copy the public key to the keys subdirectory of the inventory repo
    # if you have generated your key with the above it will be
    cp ~/.ssh/id_ed25519.pub keys/$USER

    # add to the inventory repository
    git add keys/$USER

YAML user list
--------------

In the users.yml file, add a list item to the users variable. You should really
use your local username if you want to have a nicer playlabs experience.

.. code-block:: yaml

    users:
      # ...
      - name: yourusername
        email: your@email.com
        roles:
          ssh: sudo

Reference
=========

The users YAML document in the default repository serves as reference:

.. literalinclude:: ../playlabs/inventory_template/group_vars/all/users.yml
