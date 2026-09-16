# Ingestion Layer

The ingestion layer extracts the AmazingMart source workbook without applying business transformations and preserves the original source file in the raw data lake.

## Components

- `data_ingestion.py` — validates the workbook contract and extracts the three source sheets.
- `s3_raw.py` — uploads the unchanged source workbook to AWS S3 raw storage.

## Raw S3 layout

```text
s3://<bucket>/raw/amazingmart/ingestion_date=YYYY-MM-DD/<source-file>
```

The raw zone preserves the original source file. The ingestion date is recorded in the object key, while the object metadata records the source system, ingestion timestamp, and data zone.

## Credentials and configuration

The S3 client uses boto3's standard AWS credential provider chain. Credentials must not be committed to the repository. Use an AWS profile, environment variables, IAM role, or another supported AWS credential mechanism in the execution environment.

The bucket name is supplied to the upload function rather than hard-coded into the application.

## Retention assumption

The raw zone is treated as an immutable audit layer. This project does not configure automatic object deletion yet. A production deployment should define an S3 Lifecycle policy based on operational, compliance, and cost requirements before enabling automatic expiration or archival.

## Responsibility boundary

This layer does not clean, deduplicate, join, or reshape business data. Those responsibilities belong to the validation and transformation stages that follow ingestion.
