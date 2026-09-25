# Docker and local developer workflow

This project uses Docker Compose to provide a reproducible local environment for the analytical warehouse, Spring Boot API, and Airflow orchestration runtime.

## Services

| Service | Purpose | Local port |
|---|---|---:|
| postgres | PostgreSQL warehouse | 5432 |
| api | Spring Boot data API | 8080 |
| airflow | Pipeline orchestration | 8081 |

The PostgreSQL service initializes the warehouse schema from db/warehouse_schema.sql when its data volume is created.

The API connects to PostgreSQL through the Compose service name postgres.

Airflow mounts the repository so its DAGs can access the existing ingestion, validation, PySpark, and warehouse modules.

## First-time setup

Copy the example environment file:

```bash
cp .env.example .env
```

Change POSTGRES_PASSWORD to a local development password.

AWS variables are only required if the Airflow raw_storage task is executed.

## Start the stack

```bash
docker compose up --build -d
```

Check service state:

```bash
docker compose ps
```

The API health endpoint is:

```text
http://localhost:8080/api/v1/health
```

Airflow is exposed at:

```text
http://localhost:8081
```

The Airflow standalone container prints the generated local login credentials in its logs:

```bash
docker compose logs airflow
```

Stop the stack:

```bash
docker compose down
```

Remove local PostgreSQL/Airflow state as well:

```bash
docker compose down -v
```

## Makefile commands

Common workflows are exposed through make:

```bash
make test
make java-test
make java-package
make docker-build
make up
make down
make logs
```

The Makefile intentionally keeps Python and Java commands separate because they have different build systems.

## Configuration and secrets

Real credentials must not be committed. .env is ignored by Git and .env.example documents the required variables.

The Compose file uses health checks and depends_on: condition: service_healthy so the API and Airflow containers wait for PostgreSQL readiness before starting. This prevents the common startup race where an application starts before the database is ready.

## Scope

This is a local development/reproducibility environment, not a production deployment. Airflow runs in standalone mode for simplicity. Production deployment would require separate Airflow components, external secret management, monitoring, resource sizing, and a production-grade metadata database configuration.
