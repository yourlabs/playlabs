postgres_current={{ project_postgres_home }}/.current
rm -rf $postgres_current
docker stop {{ project_postgres_host }}
