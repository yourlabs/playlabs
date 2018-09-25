postgres_current={{ project_postgres_home }}/.current
mkdir -p $postgres_current

docker stop {{ project_postgres_host }}
if [ -d {{ project_postgres_data_home }} -a ! -z "$(ls -A {{ project_postgres_data_home }})" ] ; then
    mv {{ project_postgres_data_home }}/* $postgres_current
fi

rm -rf {{ project_postgres_data_home }}/*

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
