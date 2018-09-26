#!/bin/bash
set -eu
export RESTIC_PASSWORD_FILE={{ project_home }}/.backup_password
export backup=""
set -x
export RESTIC_REPOSITORY={{ repo }}
pushd {{ project_home }}
{{ script_content_pre }}
restic backup $backup
{{ script_content_post }}
popd
