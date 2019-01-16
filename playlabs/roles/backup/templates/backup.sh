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

# restic code commented for posterity

set -eu
#export RESTIC_PASSWORD_FILE={{ project_home }}/.backup_password
export backup=""
export PASSPHRASE="$(<{{ project_home }}/.backup_password)"
set -x
backup_type="${BACKUP_TYPE-}"
#export RESTIC_REPOSITORY={{ repo }}
pushd {{ project_home }}
{{ script_content_pre }}

# build the line for duplicity ...
include_line=""
for name in $backup; do
    if [[ ! $name =~ ^/ ]]; then
        name="$(pwd)/$name"
    fi
    include_line="$include_line --include $name"
done
{% if backup_lftp_dsn|default(False) %}
duplicity $backup_type $include_line --exclude '**' / {{ backup_lftp_dsn }}/duplicity-{{ project_instance }}
# connect manually with
# lftp -c 'set ssl:check-hostname false;connect {{ backup_lftp_dsn }}'
{% endif %}
{{ script_content_post }}
popd
