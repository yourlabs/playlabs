[ ! -d {{ project_postgres_data_home }} ] || mv {{ project_postgres_data_home }} $postgres_current
docker start {{ project_postgres_host }}
until test -S {{ project_postgres_run_home }}/.s.PGSQL.5432; do
    sleep 1
done
sleep 3 # ugly wait until db starts up, socket waiting aint enough
mv $restore/data.dump {{ project_postgres_data_home }}/data.dump
docker exec {{ project_postgres_host }} psql -d {{ project_postgres_db }} -U {{ project_postgres_user }} -f {{ project_postgres_data_mount }}/data.dump
echo Restore happy, clearing $postgres_current and $restore/data.dump
rm -rf $postgres_current $restore/data.dump
