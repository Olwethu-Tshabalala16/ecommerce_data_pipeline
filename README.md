# E-Commerce Data Pipeline

## Problem Statement

E-commerce platforms generate large amounts of operational data, but raw operational data is not automatically suitable for reliable downstream analysis.

This project engineers an end-to-end data platform that ingests e-commerce data, preserves raw data, validates data quality, transforms the data into structured datasets, loads analysis-ready data into a PostgreSQL warehouse, orchestrates the pipeline with Apache Airflow, exposes selected warehouse data through a Spring Boot REST API, and provides reproducible local infrastructure through Docker.

The project focuses on **Data Engineering rather than final business analysis**. The resulting datasets are intended to provide a reliable foundation for analysts, data scientists, actuaries, and business stakeholders.

## Development Approach

The project is developed using an **Agile, incremental approach**. Each stage is implemented, tested, documented, and integrated before becoming a dependency for the next stage.

GitHub Issues are used to track engineering work. The implementation deliberately avoids inventing entities that are not supported by the source data.

## Source Dataset

The current implementation uses:

`(ecommerce)P1-AmazingMartEU2.xlsx`

The workbook contains:

- `ListOfOrders` — order-level information
- `OrderBreakdown` — product/order-line information
- `SalesTargets` — monthly category sales targets

### Source Grain

The natural grain of `OrderBreakdown` is:

> **One row represents one product line within an order.**

The current source does not contain payment or inventory information, so those entities are not fabricated in the warehouse.

## Architecture

```text
                    E-Commerce Workbook
                            |
                            v
                     Python Ingestion
                            |
                            v
                       AWS S3 Raw
                            |
                            v
                  Data Quality / Validation
                     |              |
                     | invalid      v
                     |         Quarantine
                     v
                 PySpark Processing
                            |
                            v
                    Curated Parquet
                            |
                            v
                 PostgreSQL Warehouse
                  Dimensional Star Schema
                            |
                            v
                 Spring Boot REST API
                            
Apache Airflow  ---> orchestrates pipeline dependencies
Docker          ---> reproducible local environment
Makefile        ---> standard developer commands
GitHub Actions  ---> automated tests and build verification
```

### Architectural Responsibilities

| Layer | Responsibility | Technology |
|---|---|---|
| Source | Provide operational e-commerce data | Excel |
| Ingestion | Extract and preserve source information | Python |
| Raw Storage | Preserve ingested source data | AWS S3 |
| Data Quality | Validate records and isolate problematic data | Python / SQL |
| Processing | Transform and standardise validated data | Python / PySpark |
| Curated Data | Store transformed datasets | Parquet / S3-compatible storage |
| Warehouse | Store analysis-ready dimensional data | PostgreSQL |
| API | Provide controlled access to selected warehouse data | Java / Spring Boot |
| Orchestration | Coordinate pipeline dependencies | Apache Airflow |
| Infrastructure | Reproducible local services | Docker / Docker Compose |
| Developer Workflow | Standardise common commands | Makefile |
| CI/CD | Automatically test and build the project | GitHub Actions |

## Warehouse Model

The current warehouse contains:

- `warehouse.dim_customer`
- `warehouse.dim_product`
- `warehouse.dim_location`
- `warehouse.dim_date`
- `warehouse.dim_ship_mode`
- `warehouse.dim_sales_target`
- `warehouse.fact_order_sales`

The central fact table preserves the source order-line grain:

> **One fact row represents one product line within an order.**

Measures include:

- quantity
- sales
- profit
- discount

Dimension keys are deterministic and the warehouse applies foreign-key and measure constraints.

## Transformation Layer

PySpark produces the curated dimensional datasets:

```text
dim_customer
dim_product
dim_location
dim_date
dim_ship_mode
dim_sales_target
fact_order_sales
```

The transformation preserves order-line grain and uses deterministic dimension keys derived from natural attributes.

The latest verified curated row counts are:

| Dataset | Rows |
|---|---:|
| dim_customer | 792 |
| dim_product | 1,810 |
| dim_location | 1,001 |
| dim_date | 1,436 |
| dim_ship_mode | 4 |
| dim_sales_target | 144 |
| fact_order_sales | 8,043 |

## Spring Boot API

The backend follows:

```text
Controller
    |
    v
Service
    |
    v
Repository
    |
    v
PostgreSQL Warehouse
```

Current API resources include:

- `GET /api/v1/products`
- `GET /api/v1/customers`
- `GET /api/v1/orders/lines`
- `GET /api/v1/metadata`
- `GET /api/v1/health`

The API uses Maven for dependency management, testing, and packaging.

Payment and inventory endpoints are intentionally absent because those entities are not present in the source dataset.

## Airflow Orchestration

The DAG is:

`ecommerce_data_pipeline`

The current dependency graph is:

```text
extract ──────> validate ──────> transform ──> quality ──> warehouse_load
    |
    └─────────> raw_storage ────────^
```

The DAG coordinates:

1. source extraction
2. validation
3. raw S3 storage
4. PySpark transformation
5. curated-data quality checks
6. PostgreSQL warehouse loading

The DAG is configured for daily scheduling with catch-up disabled.

## Docker

Docker Compose provides a reproducible local environment containing:

| Service | Purpose | Default Port |
|---|---|---:|
| PostgreSQL | Analytical warehouse | 5432 |
| Spring Boot API | Data access API | 8080 |
| Airflow | Pipeline orchestration | 8081 |

First-time setup:

```bash
cp .env.example .env
```

Then:

```bash
docker compose up --build -d
```

Useful commands:

```bash
docker compose ps
docker compose logs airflow
docker compose down
```

Real credentials belong in `.env`, which is excluded from version control.

See `docs/docker.md` for the complete local workflow.

## Makefile

Common development workflows are standardised through the Makefile:

```bash
make test
make java-test
make java-package
make docker-build
make up
make down
make logs
make validate
make profile
make transform
```

This keeps Python, Java, Docker, and pipeline commands consistent across development environments.

## Testing and CI/CD

GitHub Actions automatically verifies the project on pushes to `main` and pull requests targeting `main`.

The CI workflow covers:

- Python `pytest` tests
- Java/Spring Boot tests
- Maven package verification
- PostgreSQL warehouse constraint tests
- Docker Compose configuration validation
- Spring Boot Docker image builds

The warehouse CI job specifically verifies important fact-table constraints, including valid quantity and discount ranges.

## Core Data Engineering Concepts

The project demonstrates:

- data profiling
- data ingestion
- data validation
- data-quality rules
- quarantine of problematic records
- ETL / ELT concepts
- batch processing
- object storage
- dimensional modelling
- star-schema design
- PySpark transformation
- Parquet
- PostgreSQL warehousing
- pipeline orchestration
- metadata and lineage
- idempotent processing
- REST API development
- automated testing
- containerisation
- CI/CD
- developer workflow automation

## Project Structure

```text
.
├── airflow/              # Airflow DAGs
├── db/                   # Source and warehouse SQL schemas
├── docker/               # Container-specific configuration
├── docs/                 # Architecture and operational documentation
├── ingestion/            # Source ingestion and S3 storage
├── transformation/       # PySpark processing
├── validation/            # Data-quality validation and quarantine
├── warehouse/             # PostgreSQL warehouse loader
├── src/                   # Spring Boot API
├── tests/                 # Python tests
├── Dockerfile             # Spring Boot container image
├── compose.yaml           # Local multi-service environment
├── Makefile               # Standard development commands
├── pom.xml                # Maven/Spring Boot build
├── requirements.txt       # Python dependencies
└── .github/workflows/     # CI/CD automation
```

## Engineering Objective

The objective is to demonstrate how raw operational e-commerce data can be engineered into reliable, analysis-ready data through a reproducible platform.

The project therefore emphasises:

- preserving source data
- explicit data-quality rules
- traceable transformations
- dimensional modelling
- reliable warehouse loading
- orchestration of dependent stages
- controlled API access
- reproducible infrastructure
- automated verification

The platform is an engineering foundation for downstream analytical work rather than an end-user business intelligence application.
