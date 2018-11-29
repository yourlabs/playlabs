Projects deployments and lifecycles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

::

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
