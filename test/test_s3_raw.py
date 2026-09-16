"""Tests for the S3 raw data lake storage layer."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ingestion.s3_raw import build_raw_key, upload_raw_file


def test_build_raw_key_preserves_source_filename() -> None:
    timestamp = datetime(2026, 9, 16, 1, 30, tzinfo=timezone.utc)

    key = build_raw_key("source.xlsx", timestamp)

    assert key == "raw/amazingmart/ingestion_date=2026-09-16/source.xlsx"


def test_upload_raw_file_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        upload_raw_file(tmp_path / "missing.xlsx", "bucket")


def test_upload_raw_file_rejects_empty_bucket(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    source.write_bytes(b"source data")

    with pytest.raises(ValueError, match="bucket"):
        upload_raw_file(source, "   ")


def test_upload_raw_file_uses_raw_key_and_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.xlsx"
    source.write_bytes(b"unchanged source data")
    timestamp = datetime(2026, 9, 16, 1, 30, tzinfo=timezone.utc)
    client = Mock()

    with patch("ingestion.s3_raw.boto3.client", return_value=client):
        result = upload_raw_file(source, "ecommerce-data", timestamp)

    expected_key = "raw/amazingmart/ingestion_date=2026-09-16/source.xlsx"
    assert result == f"s3://ecommerce-data/{expected_key}"
    client.upload_file.assert_called_once_with(
        str(source),
        "ecommerce-data",
        expected_key,
        ExtraArgs={
            "Metadata": {
                "source-system": "amazingmart",
                "ingestion-timestamp": timestamp.isoformat(),
                "data-zone": "raw",
            }
        },
    )
