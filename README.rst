0. Bootstrap
============

"Boostrap" means installng your own user with your ssh key, sudo access and all
necessary dependencies to execute ansible.

Run::

    playlabs boostrap root@somehost
    playlabs boostrap user@somehost  # will use sudo

Then, it will execute the bootstrap.yml playbook with the right options.
