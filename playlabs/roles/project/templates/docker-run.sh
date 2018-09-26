#!/bin/bash -eux
docker rm -f {{ project_instance }} || echo could not rm container
docker run -d --name {{ project_instance }} --restart unless-stopped \
    {% for plugin in project_plugins %}
    {%- if 'project_' + plugin + '_docker_options' in hostvars[inventory_hostname] %}
    {{ lookup('vars', 'project_' + plugin + '_docker_options') }} \
    {% endif -%}
    {%- endfor %}
    -v {{ project_log_home }}:{{ project_log_mount }} \
    {% for key, value in project_env.items() %}
    -e {{ key }}='{% if value.replace is defined %}{{ value.replace("'", "\\'") }}{% else %}{{ value }}{% endif %}' \
    {% endfor %}
    {{ project_image }} {% if project_secure and 'DOCKER_RUN_SECURE' in project_image_env %}{{ project_image_env['DOCKER_RUN_SECURE'] }}{% elif not project_secure and 'DOCKER_RUN' in project_image_env %}{{ project_image_env['DOCKER_RUN'] %}{% endif %}
docker network connect {{ project_instance }} {{ project_instance }}
{% for network in project_networks -%}
docker network connect {{ network }} {{ project_instance }}
{% endfor %}
