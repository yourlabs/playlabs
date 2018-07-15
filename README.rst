This repository contains playbooks for YourLabs & partners infrastructure. It
should support any distro and do as much as possible in docker.

Getting started
===============

Make sure you have working and up to date ansible and git commands.

Clone the playbooks::

    $ git clone git@git.yourlabs.org:oss/playbooks.git

Clone your inventory next to your playbooks directory.

Rather than organizing around playbooks, we organize around roles, and have one
playbook to apply any of them: role.yml. Example::

   ANSIBLE_STDOUT_CALLBACK=debug ansible-playbook --become --become-user=root --become-method=sudo -e role=ssh -i inventory -v playbooks/role.yml

To make a role apply to a host, add the host to a group that contains the role
name. Example:

.. code-block:: yaml

    all:
      hosts:
        git:
          fqdn: git.example.com

      children:
        # make ssh, gitlab and nginx roles apply on git host
        ssh-gitlab-nginx:
          hosts:
            git:

0. Bootstrap
============

Bootstrap means installing your user with your ssh key and make it a sudoer
without password, along with ansible runtime dependencies on the server. This
enables executing other playbooks unattended.

Examples::

    # Example for scaleway debian based box
    ansible-playbook --user root -i yourlabs/inventory.yml -e update_packages='apt update -y' -e install_python='apt install -y python3' bootstrap.yml

    # Example for online debian based box
    ansible-playbook --become-user root --become-method sudo --become --ask-sudo-pass -i yourlabs/inventory.yml -e update_packages='apt update -y' -e install_python='apt install -y python3' -l kube bootstrap.yml

1. Users and sshd
=================

Create accounts for your friends, beware this playbook sets SSH port to 2222
and disables root and password login ! This way, you will not need to specify a
non-default port for gitea or gitlab because we will bind their ssh server on
port 22.

This requires such variables in the inventory::

    users:
    - name: jpic
      first_name: James
      last_name: Pic
      email: jpic@yourlabs.org
      roles:
        sentry: superuser
        ssh: sudo
      key: 'ssh-rsa .... bla@foo'

    # Those are in a separate variable so you have the choice to put the users
    # variable unencrypted which should make diffs easier to read.
    users_passwords:
      jpic: somepassword

Example::

    ansible-playbook --user root -i yourlabs/inventory.yml -e role=ssh -v role.yml

2. Install docker
=================

The docker.yml playbook installs docker and the python modules for ansible's
``docker_*`` modules. It will add ``users`` to the ``docker`` group. For now we
aren't exposing the mail server to the internet, so we'll need this variable to
enforce local resolution of our mail_dns::

    dns_local_resolve: [{{ mail_dns }}]

3. Firewall
===========

This depends on docker, so install docker first.

Firewall rules are maintained in the firewall.yml playbook, which autorizes
ports 22, 2222, 80 and 443 by default.

4. Install duplicity
====================

The duplicity.yml playbook installs the GPG key defined in the inventory, and
installs duplicity to make backups. Requires variables::

    backup_ftp_password: yourftppassword
    backup_dsn: ftp://username@host

    gpg_id: 1231971231239817239817298317239817983172
    gpg_email: yourgpgemail
    gpg_private_key: |
      -----BEGIN PGP PRIVATE KEY BLOCK-----

      oaseuteoasntuhseoathusoaethusoathusoteuh
      aosuetoasnuethoaesuntoahesuntoaheustoahu
      -----END PGP PRIVATE KEY BLOCK-----
    gpg_public_key: |
      -----BEGIN PGP PUBLIC KEY BLOCK-----

      oaseuteoasntuhseoathusoaethusoathusoteuh
      aosuetoasnuethoaesuntoahesuntoaheustoahu
      -----END PGP PUBLIC KEY BLOCK-----

To get the gpg variable data, run::

    gpg --full-generate-key

This will make you choose an email address and will output a key id,
respectively for gpg_email and gpg_id.

Export your private key for gpg_private_key with::

    gpg --armor --export-secret-keys yourkeyid

Export your public key for gpg_public_key with::

    gpg --armor --export yourkeyid

Now you can run the duplicity.yml playbook.

5. Install docker-dns-gen
=========================

The dns.yml playbook installs a docker-dns-gen container with all features that
come with it.

This allows certificates generated with nginx-letsencrypt to be usable on
internal domains.

Also, this adds a dynamic DNS server which configures itself with environment
variables from other containers and zero configuration.

To force the server to use this DNS server for certain DNS names (through
dnsmasq), use a comma separated list of dns names in
``dns_local_resolve.split``.

6. Installation nginx
=====================

The nginx.yml playbook installs a nginx-gen and a nginx-letsencrypt companion
container.

Note that you can switch to use the staging letsencrypt server by overriding
the letsencrypt_uri variable (see roles/nginx/defaults for an example).

Requires variable::

    # Email to use for letsencrypt registration
    letsencrypt_email: your@email.com

7. Install Mail server
======================

Requires in any case::

    mail_dns: mail.example.com

poste.io
--------

To use poste.io, set variable::

    poste_image: analogic/poste.io

**OR** to use poste.io pro, set variable::

    poste_image: poste.io/mailserver
    poste_pro_username: yourusername
    poste_pro_password: yourpassword

Run the mail role, open the mail_dns with your browser and setup the password
you want for the admin, report it in ``mail_postmaster_password``. Also set
``mail_postmaster_email`` to ``admin@{{ mail_dns }}``

tvial/docker-mailserver
-----------------------

Otherwise, the mail role will use tvial/docker-mailserver, fully unattended, in
which case you need to set the following variables **prior** to running the
role::

    mail_postmaster_email: postmaster@mail.yourdns.com
    mail_postmaster_password: yourpostmasterpassword

Then, you can use the mail_account creation role to create accounts.

8. Install munin
================

The munin.yml playbook sets up a munin server. This is required before
executing any playbook which sets up a postgresql container, because postgresql
containers are setup with monitoring. Requires::

    munin_email: munin@your.mail.com
    munin_email_password: somepassword
    munin_dns: munin.yourdns.com

9. Install sentry
=================

The sentry role installs a sentry server, requires::

    sentry_dns: sentry.yourdns.com
    sentry_email: sentry@yourmail.com
    sentry_email_password: yoursentryemailpassword
    sentry_postgresql_password: yoursentrypostgrespasswor
    sentry_secret_key: yousentrysecretkey

You can generate a secret key with::

    python -c 'import random; print("".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)]))'

Example command::

   ANSIBLE_STDOUT_CALLBACK=debug ansible-playbook --become --become-user=root --become-method=sudo -e role=sentry -i inventories/yourlabs/inventory -v playbooks/role.yml

10. Install netdata
===================

Installs a protected netdata instance, requires::

    netdata_dns: netdata.example.com
    netdata_email: netdata@{{ mail_dns }}
    netdata_email_password: somepassword

This will automatically be protected with htaccess, allowing users defined in
the inventory.

11. Install docker registry
===========================

The registry role installs a protected docker registry instance, requires::

    registry_dns: docker.example.com

This will automatically be protected with htaccess, allowing users defined in
the inventory.

Example command::

    ANSIBLE_STDOUT_CALLBACK=debug ansible-playbook --become --become-user=root --become-method=sudo -e role=registry -i inventories/yourlabs/inventory -v playbooks/role.yml

10. Gitea
=========

The gitea role installs a gitea server with ssh bound on port 22 for kewl git
urls. Requires::

    gitea_app_name: YourCompany
    gitea_dns: git.yourdns.com
    gitea_email: git@{{ mail_dns }}
    gitea_email_password: giteaemailpassword
    gitea_server_LFS_JWT_SECRET: giteasecr
    gitea_security_SECRET_KEY: asothu
    gitea_security_INTERNAL_TOKEN: aoeu

Example command::

   ANSIBLE_STDOUT_CALLBACK=debug ansible-playbook --become --become-user=root --become-method=sudo -e role=gitea -i inventories/yourlabs/inventory -v playbooks/role.yml

11. Drone CI
============

The drone roles installs a drone server using gitea, requires::

    drone_dns: ci.example.com
    drone_secret: yourdronesecret
    drone_postgresql_password: yourpostgrespassword

Example command::

   ANSIBLE_STDOUT_CALLBACK=debug ansible-playbook -e role=drone -i inventories/yourlabs/inventory -v playbooks/role.yml

10. MRS
=======

Le playbook mrs.yml déploie le site mais requierts 2 variables: nom de
l'instance (staging, production) et nom de l'image docker, example::

    ANSIBLE_VAULT_PASSWORD=.vault ansible-playbook -e image=betagouv/mrs:latest -e instance=staging mrs.yml

A. Developpement
================

Role backup: automatisation de backup
-------------------------------------

Le role backup permet d'ajouter un script de backup avec une telle tache::

  - name: Install backup scripts
    vars:
      unit_name: backup-passbolt
      unit_description: Passbolt backup
      script_path: /data/{{ passbolt_dns }}/backup.sh
      script_content: |
        #!/bin/bash -eux
        export passbolt_dump=/data/{{ passbolt_dns }}/backup/passbolt.sql
        mkdir -p ${passbolt_dump%/*}
        docker exec -t passbolt-mysql mysqldump -upassbolt -p{{ passbolt_mysql_password }} passbolt &> $passbolt_dump
        export FTP_PASSWORD="{{ backup_ftp_password }}"
        /usr/bin/duplicity \
          --encrypt-key={{ gpg_id }} \
          /data/{{ passbolt_dns }}/backup \
          {{ backup_host }}/mrs/passbolt
        rm -rf $passbolt_dump
    include_role:
      name: backup

Role mail: création de comptes emails
-------------------------------------

Le role mail permet d'ajouter un compte postfix avec une telle tache::

  - name: Install postmaster email account
    vars:
      email: '{{ mail_postmaster_email }}'
      password: '{{ mail_postmaster_password }}'
    include_role:
      name: mail

Role munin_postgresql: monitoring munin pour instance postgresql
----------------------------------------------------------------

Ce role permet d'ajouter le monitoring d'une instance de postgresql. Il faut
pour cela exposer le socket unix de postgresql sur l'hote, example::

  docker_container:
    name: your-postgres
    volumes:
    - '/data/your-postgres/postgresql/run:/var/run/postgresql'
    env:
      POSTGRES_PASSWORD: '{{ your_password }}'
      POSTGRES_USER: you

  - name: Install munin monitoring for postgresql
    vars:
      postgresql_instance: your-postgres
      postgresql_user: you
      postgresql_password: '{{ your_password }}'
      postgresql_host: /data/your-postgres/postgresql/run
    include_role:
      name: munin_postgresql

Après plusieurs minutes, vous devriez voir votre instance postgresql dans
munin.

Role nginx_htpasswd: sécuriser un domaine avec admin_passwords
--------------------------------------------------------------

Ce role utilise le dictionnaire admin_passwords pour sécuriser un DNS avec un
htaccess au niveau de docker-gen. La variable admin_passwords devrait être
chiffrée avec ansible-vault, mais ça n'est pas obligatoire. Example::

  - name: Install netdata htaccess
    vars:
      dns: '{{ netdata_dns }}'
    include_role:
      name: nginx_htpasswd

B. Autres Services
==================

Playbook passbolt.yml: partage de mot de passes Open Source
-----------------------------------------------------------

The passbolt.yml playbook installs Passbolt, a shared password management
service. Requires variables::

    passbolt_dns: passbolt.example.com
    passbolt_email: passbolt@{{ mail_dns }}
    passbolt_email_password: yourpassboltemailpassword
    passbolt_mysql_password: yourpassboltmysqlpassword
    passbolt_salt: yourpassboltsalt
    passbolt_cipherseed: yourpassboltcipherseed
    passbolt_mysql_root_password: yourpassboltmysqlrootpassword
