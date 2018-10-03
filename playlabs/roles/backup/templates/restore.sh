#!/bin/bash
set -eu
export RESTIC_PASSWORD_FILE={{ project_home }}/.backup_password
set -x
export RESTIC_REPOSITORY={{ repo }}

pushd {{ project_home }}
{% if backup_lftp_dsn|default(False) %}
if [ ! -d $RESTIC_REPOSITORY ]; then
    echo 'Repository not found ! geting from ftp'
    lftp -c 'set ssl:check-hostname false;connect {{ backup_lftp_dsn }}; mirror -v {{ project_instance }}/restic {{ project_home }}/restic'
fi
{% else %}
echo 'FTP not available: backup_lftp_dsn inventory variable not set'
echo 'Do NOT rm the restic directory'
{% endif %}
if [ -z "${1-}" ]; then
    restic snapshots
    exit 0
fi
export restore={{ project_home }}/restore
{{ restore_content_pre }}
restic restore $1 --target $restore
{{ restore_content_post }}
popd
