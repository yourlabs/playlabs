Managing infra variables in the inventory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
