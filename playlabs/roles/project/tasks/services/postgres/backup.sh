docker start {{ project_postgresql_host }}
docker exec {{ project_postgresql_host }} pg_dumpall -U postgres -c -f /run/postgresql/data.dump
docker logs {{ project_instance }} &> project.log || echo "Couldn't get logs from instance"
docker logs {{ project_postgresql_host }} &> postgres.log
