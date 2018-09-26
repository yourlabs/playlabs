if [ -d {{ project_postgres_data_home }} ] && docker start {{ project_postgres_host }}; then
  docker start {{ project_postgres_host }}
  docker logs {{ project_postgres_host }} >> {{ project_log_home }}/postgres.log
  docker exec {{ project_postgres_host }} pg_dumpall -U {{ project_postgres_user }} -c -f {{ project_postgres_data_mount }}/data.dump
  backup="$backup {{ project_postgres_data_home }}/data.dump"
fi
