mv restore/data.dump postgresql/run/data.dump
docker stop {{ project_postgresql_host }}
rm -rf postgresql/data/*
docker start {{ project_postgresql_host }}
until test -S postgresql/run/.s.PGSQL.5432; do
    sleep 1
done
echo ugly wait until db starts up, socket waiting aint enough
sleep 3
docker exec {{ project_postgresql_host }} psql -U postgres -f /run/postgresql/data.dump
