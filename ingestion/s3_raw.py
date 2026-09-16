"""AWS S3 raw data lake storage for source files."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import boto3

SOURCE_NAME = "amazingmart"
RAW_PREFIX = "raw"


def build_raw_key(source_file: str, ingestion_time: datetime | None = None) -> str:
    """Build a date-partitioned S3 key while preserving the original filename."""
    timestamp = ingestion_time or datetime.now(timezone.utc)
    ingestion_date = timestamp.strftime("%Y-%m-%d")
    return f"{RAW_PREFIX}/{SOURCE_NAME}/ingestion_date={ingestion_date}/{source_file}"


def upload_raw_file(
    file_path: Path,
    bucket_name: str,
    ingestion_time: datetime | None = None,
) -> str:
    """Upload an unchanged source file to the S3 raw zone.

    AWS credentials and region are resolved by boto3's standard credential
    provider chain. No credentials are stored in source code.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Source file not found: {file_path}")
    if not bucket_name.strip():
        raise ValueError("S3 bucket name must not be empty")

    timestamp = ingestion_time or datetime.now(timezone.utc)
    key = build_raw_key(file_path.name, timestamp)
    s3 = boto3.client("s3")

    s3.upload_file(
        str(file_path),
        bucket_name,
        key,
        ExtraArgs={
            "Metadata": {
                "source-system": SOURCE_NAME,
                "ingestion-timestamp": timestamp.isoformat(),
                "data-zone": "raw",
            }
        },
    )

    return f"s3://{bucket_name}/{key}"
