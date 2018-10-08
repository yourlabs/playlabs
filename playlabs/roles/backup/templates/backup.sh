#!/bin/bash
set -eu
export RESTIC_PASSWORD_FILE={{ project_home }}/.backup_password
export backup=""
set -x
export RESTIC_REPOSITORY={{ repo }}
pushd {{ project_home }}
{{ script_content_pre }}
restic backup $backup
{% if backup_lftp_dsn|default(False) %}
lftp -c 'set ssl:check-hostname false;connect {{ backup_lftp_dsn }}; mkdir -p {{ project_instance }}; mirror -Rv {{ project_home }}/restic {{ project_instance }}/restic'
{% endif %}
{{ script_content_post }}
popd
