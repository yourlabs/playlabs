#!/bin/bash
set -eu
#export RESTIC_PASSWORD_FILE={{ project_home }}/.backup_password
set -x
#export RESTIC_REPOSITORY={{ repo }}

pushd {{ project_home }}
export PASSPHRASE="$(<{{ project_home }}/.backup_password)"
{% if backup_lftp_dsn|default(False) %}
if [ -z "${1-}" ]; then
    duplicity collection-status {{ backup_lftp_dsn }}/duplicity-{{ project_instance }}
    exit 0
fi
export restore={{ project_home }}/restore
rm -rf $restore
{{ restore_content_pre }}
duplicity restore --time "$1" {{ backup_lftp_dsn }}/duplicity-{{ project_instance }} $restore
{{ restore_content_post }}
popd
{% else %}
echo 'FTP not available: backup_lftp_dsn inventory variable not set'
{% endif %}
