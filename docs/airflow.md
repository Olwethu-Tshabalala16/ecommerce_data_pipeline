# Airflow orchestration

## DAG

The project exposes one Airflow DAG:

- DAG ID: `ecommerce_data_pipeline`
- Schedule: `@daily`
- Catchup: disabled
- Maximum active runs: 1
- Retries: 2 with a 5-minute delay

The DAG deliberately orchestrates existing project components rather than moving business logic into the DAG.

## Task flow

```text
extract
   |
   +--------------------+
   |                    |
   v                    v
validate            raw_storage
   |                    |
   +---------+----------+
             v
         transform
             |
             v
          quality
             |
             v
       warehouse_load
```

### Task responsibilities

1. **extract** — reads the configured workbook with the existing ingestion module and records run metadata.
2. **validate** — runs the existing validation pipeline and allows the known exact duplicate order-line rule to remain quarantined.
3. **raw_storage** — uploads the unchanged workbook to the S3 raw zone.
4. **transform** — calls the existing PySpark transformation layer and writes curated Parquet datasets.
5. **quality** — verifies all required curated datasets exist, are non-empty, and retain the row counts produced by transformation.
6. **warehouse_load** — calls the existing transactional PostgreSQL warehouse loader.

Airflow therefore controls dependency, retry, scheduling, and observability while the existing modules remain responsible for ingestion, validation, transformation, and loading.

## Required environment

The Airflow runtime needs:

- `ECOMMERCE_SOURCE_FILE` — optional; defaults to the project workbook at the repository root.
- `RAW_S3_BUCKET` — required; target bucket for the raw source upload.
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and AWS region configuration as required by the standard boto3 credential chain.
- `WAREHOUSE_DB` — optional; defaults to `ecommerce_dw`.
- `WAREHOUSE_USER` — optional; defaults to `postgres`.
- `WAREHOUSE_HOST` — optional.
- `WAREHOUSE_PORT` — optional; defaults to `5432`.
- `WAREHOUSE_PASSWORD` — optional.

Secrets must be supplied through the Airflow/runtime environment rather than committed to Git.

## Local Airflow installation

Airflow should be installed in a dedicated virtual environment rather than the project's normal Python environment. The current project uses Python 3.14, which is supported by the current Airflow 3.3 release.

Use the Airflow release's official constraints file when installing:

```bash
AIRFLOW_VERSION=3.3.2
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

Then configure the DAG directory so Airflow discovers `airflow/dags` from this repository. For a local development setup, `AIRFLOW_HOME` can point to a project-specific Airflow directory.

The DAG is intended for local development/testing at this stage. Docker-based service orchestration is handled by the later infrastructure issue.

## Operational assumptions

- The source workbook is batch-oriented and currently represents the available source snapshot.
- The raw upload preserves the original workbook.
- The warehouse loader performs a transactional full refresh of the current curated snapshot.
- Curated Parquet output is written to the repository's `curated/` directory. The later containerisation work must provide shared storage if Airflow tasks run in separate containers or workers.
- A failed task is retried twice. A failed upstream task prevents downstream tasks from running.
- `max_active_runs=1` prevents overlapping warehouse refreshes for this batch pipeline.
