#!/bin/bash
if [ -z "$BACKUP_FORCE" ]; then
  cat <<EOF
This script is not safe to run multiple instances at the same time.
You need to set the BACKUP_FORCE env var for the script to continue.

Or even better, use the systemd unit, that will garantee that the
script is not executed multiple times at the same time:

    systemctl start {{ unit_name }}
    systemctl status {{ unit_name }}
    journalctl -fu {{ unit_name }}

Now, this script will execute the following for you:

  systemctl start {{ unit_name }}
EOF
  systemctl start backup-mrs-staging
  exit 0
fi

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
