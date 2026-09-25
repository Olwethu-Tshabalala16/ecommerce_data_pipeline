"""Airflow orchestration for the AmazingMart e-commerce data pipeline.

Airflow coordinates the existing pipeline components. Business transformation,
validation, and warehouse logic remain in their dedicated project modules.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pendulum
from airflow.sdk import dag, get_current_context, task


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SOURCE_FILE = Path(
    os.getenv(
        "ECOMMERCE_SOURCE_FILE",
        str(PROJECT_ROOT / "(ecommerce)P1-AmazingMartEU2.xlsx"),
    )
)
S3_BUCKET = os.getenv("RAW_S3_BUCKET")


@dag(
    dag_id="ecommerce_data_pipeline",
    schedule="@daily",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "olwethu",
        "retries": 2,
        "retry_delay": pendulum.duration(minutes=5),
    },
    tags=["ecommerce", "data-engineering", "batch"],
    description="Orchestrate ingestion, validation, raw storage, transformation, quality, and warehouse loading.",
)
def ecommerce_pipeline():
    @task
    def extract() -> dict:
        """Extract the source workbook and return run metadata."""
        from ingestion.data_ingestion import ingest_workbook

        result = ingest_workbook(SOURCE_FILE)
        context = get_current_context()
        dag_run = context["dag_run"]

        metadata = {
            "dag_id": dag_run.dag_id,
            "run_id": dag_run.run_id,
            "source_file": result.source_file,
            "ingested_at": result.ingested_at,
            "source_path": str(SOURCE_FILE),
        }

        print(f"Pipeline run metadata: {metadata}")
        return metadata

    @task
    def validate(extract_metadata: dict) -> dict:
        """Run source validation and quarantine expected duplicate order lines."""
        from validation.data_validation import run_validation_pipeline

        result = run_validation_pipeline(
            workbook_path=SOURCE_FILE,
            fail_on_error=True,
            allowed_failed_rules={"breakdown_exact_duplicates"},
        )

        summary = result.summary
        print(
            "Validation status=%s, quarantined=%s, failed_rules=%s"
            % (
                result.validation_status,
                summary.get("total_quarantined_records"),
                summary.get("failed_rules"),
            )
        )

        return {
            **extract_metadata,
            "validation_status": result.validation_status,
            "validation_report": str(result.report_path),
            "quarantined_records": summary.get("total_quarantined_records", 0),
        }

    @task
    def raw_storage(extract_metadata: dict) -> str:
        """Upload the unchanged source workbook to the S3 raw zone."""
        from ingestion.s3_raw import upload_raw_file

        if not S3_BUCKET:
            raise RuntimeError("RAW_S3_BUCKET Airflow environment variable is required.")

        from datetime import datetime, timezone

        ingested_at = datetime.fromisoformat(extract_metadata["ingested_at"])
        uri = upload_raw_file(
            file_path=SOURCE_FILE,
            bucket_name=S3_BUCKET,
            ingestion_time=ingested_at.astimezone(timezone.utc),
        )

        print(f"Raw source stored at: {uri}")
        return uri

    @task
    def transform() -> dict[str, int]:
        """Build the curated Parquet datasets using the existing PySpark layer."""
        from transformation.pyspark_transformation import (
            create_spark_session,
            transform_validated_data,
        )

        spark = create_spark_session()
        try:
            curated = transform_validated_data(
                spark=spark,
                workbook_path=SOURCE_FILE,
                output_dir=PROJECT_ROOT / "curated",
            )
            counts = {name: dataframe.count() for name, dataframe in curated.items()}
            print(f"Curated dataset row counts: {counts}")
            return counts
        finally:
            spark.stop()

    @task
    def quality(curated_counts: dict[str, int]) -> dict[str, int]:
        """Verify that curated datasets are present and non-empty before loading."""
        from pyspark.sql import SparkSession

        required = {
            "dim_customer",
            "dim_product",
            "dim_location",
            "dim_date",
            "dim_ship_mode",
            "dim_sales_target",
            "fact_order_sales",
        }

        missing = sorted(
            name
            for name in required
            if not (PROJECT_ROOT / "curated" / name).exists()
        )
        if missing:
            raise FileNotFoundError(f"Missing curated datasets: {missing}")

        empty = {name: count for name, count in curated_counts.items() if count == 0}
        if empty:
            raise ValueError(f"Curated datasets are empty: {empty}")

        spark = SparkSession.builder.master("local[*]").appName(
            "ecommerce-curated-quality"
        ).getOrCreate()
        try:
            verified_counts = {
                name: spark.read.parquet(str(PROJECT_ROOT / "curated" / name)).count()
                for name in sorted(required)
            }
        finally:
            spark.stop()

        if verified_counts != curated_counts:
            raise RuntimeError(
                f"Curated row-count mismatch: transform={curated_counts}, "
                f"verified={verified_counts}"
            )

        if verified_counts["fact_order_sales"] <= 0:
            raise ValueError("fact_order_sales contains no order-line records.")

        print(f"Curated quality checks passed: {verified_counts}")
        return verified_counts

    @task
    def warehouse_load(verified_counts: dict[str, int]) -> dict[str, int]:
        """Load the verified curated snapshot into PostgreSQL."""
        from warehouse.load_warehouse import load

        load()
        print(f"Warehouse load completed for curated counts: {verified_counts}")
        return verified_counts

    extracted = extract()
    validated = validate(extracted)
    stored_raw = raw_storage(extracted)
    curated = transform()
    verified = quality(curated)
    loaded = warehouse_load(verified)

    extracted >> validated
    validated >> curated
    stored_raw >> curated
    curated >> verified >> loaded


ecommerce_pipeline()
