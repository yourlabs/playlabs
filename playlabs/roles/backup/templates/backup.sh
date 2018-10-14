#!/bin/bash
if [ -z "$BACKUP_FORCE" ]; then
  cat <<EOF
This script is not safe to run multiple instances at the same time.
You need to set the BACKUP_FORCE env var for the script to continue.

Or even better, use the systemd unit, that will garantee that the
script is not executed multiple times at the same time:

    systemctl start --wait {{ unit_name }}
    systemctl status {{ unit_name }}
    journalctl -fu {{ unit_name }}

Please upgrade to the above. Meanwhile, the script will deal with systemd for
you.
EOF
  set -eux
  journalctl -fu {{ unit_name }} &
  journalpid="$!"
  systemctl start --wait {{ unit_name }}
  retcode="$?"
  kill $journalpid
  exit $retcode
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
