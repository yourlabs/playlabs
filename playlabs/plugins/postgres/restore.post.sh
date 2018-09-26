[ ! -d {{ project_postgres_data_home }} ] || mv {{ project_postgres_data_home }} $postgres_current
mv $restore/data.dump {{ project_postgres_data_home }}/data.dump
docker start {{ project_postgres_host }}
until test -S {{ project_postgres_run_home }}/.s.PGSQL.5432; do
    sleep 1
done
echo ugly wait until db starts up, socket waiting aint enough
sleep 3
docker exec {{ project_postgres_host }} psql -U {{ project_postgres_user }} -f {{ project_postgres_data_mount }}/data.dump
echo Restore happy, clearing $postgres_current and $restore/data.dump
rm -rf $postgres_current $restore/data.dump
