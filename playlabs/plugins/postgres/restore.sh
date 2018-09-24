mv restore/data.dump postgres/run/data.dump
docker stop {{ project_postgres_host }}
rm -rf postgres/data/*
docker start {{ project_postgres_host }}
until test -S postgres/run/.s.PGSQL.5432; do
    sleep 1
done
echo ugly wait until db starts up, socket waiting aint enough
sleep 3
docker exec {{ project_postgres_host }} psql -U {{ project_postgres_user }} -f /run/postgres/data.dump
