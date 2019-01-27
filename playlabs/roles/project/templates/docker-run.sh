#!/bin/bash -eux
docker rm -f {{ project_instance }} || echo could not rm container
docker run -d --name {{ project_instance }} --restart unless-stopped \
    --log-driver journald \
    {% for plugin in project_plugins %}
    {%- if 'project_' + plugin + '_docker_options' in hostvars[inventory_hostname] %}
    {{ lookup('vars', 'project_' + plugin + '_docker_options') }} \
    {% endif -%}
    {%- endfor %}
    -v {{ project_log_home }}:{{ project_log_mount }} \
    {% for key, value in project_env.items() %}
    -e {{ key }}='{% if value.replace is defined %}{{ value.replace("'", "\\'") }}{% else %}{{ value }}{% endif %}' \
    {% endfor %}
    $(<{{ project_home }}/docker-image)
docker network connect {{ project_instance }} {{ project_instance }}
{% for network in project_networks -%}
docker network connect {{ network }} {{ project_instance }}
{% endfor %}

docker logs {{ project_instance }}
