# E-Commerce Data Pipeline

## Problem Statement

E-commerce platforms generate large amounts of operational data. Although this data is valuable, raw operational data is not automatically suitable for reliable downstream analysis.

Real-world data can contain missing values, duplicate records, invalid values, inconsistent formats, broken relationships between entities, and other quality issues. Data also needs to be stored in a way that preserves raw information while making processed data efficient and consistent for downstream consumers.

This project addresses that problem by engineering an end-to-end data platform that ingests e-commerce data, preserves raw data, validates data quality, transforms data into structured datasets, loads analysis-ready data into a warehouse, orchestrates the pipeline, and exposes selected data and pipeline information through an API.

The project focuses on **Data Engineering rather than final business analysis**. The Data Engineer is responsible for building the infrastructure and pipelines that make reliable downstream analysis possible. Data Analysts, Data Scientists, Actuaries, and business stakeholders can then use the resulting datasets to answer business questions and make decisions.

## Development Approach

The project is being developed using an **Agile, incremental approach**.

The architecture describes the intended end state, but the implementation is delivered in small, testable increments rather than attempting to build the entire platform at once.

Each increment is designed to:

- solve a clearly defined engineering problem;
- produce a working and verifiable result;
- be tested before moving to the next dependency;
- document important assumptions and trade-offs;
- remain aligned with the actual source data; and
- provide a foundation for the next increment.

GitHub Issues are used to break the project into manageable engineering tasks. The implementation order may evolve as new information is discovered during profiling, validation, testing, and integration.

This means that the architecture and roadmap are **living artefacts**. They are updated when implementation evidence shows that an earlier assumption is incorrect or when a more appropriate engineering decision is identified.

The project deliberately avoids implementing unsupported entities merely to make the architecture appear larger. The warehouse and pipeline are based on the capabilities and fields actually present in the selected source dataset.

## Current Source Dataset

The current implementation uses the downloaded e-commerce workbook:

`(ecommerce)P1-AmazingMartEU2.xlsx`

The workbook contains three source sheets:

- `ListOfOrders` — order-level information
- `OrderBreakdown` — product/order-line information
- `SalesTargets` — monthly category sales targets

The natural grain of `OrderBreakdown` is:

> **One row represents one product line within an order.**

The current source data does **not** contain payment or inventory information. Therefore, payment and inventory entities are not fabricated as part of the implementation.

The source dataset has been profiled before downstream modelling. This profiling identified, among other findings, duplicate order-line records and ambiguous city-only identification. These findings inform the validation and warehouse design.

## Architecture

This project follows a **Layered Architecture**, where each layer has a defined responsibility and passes data or services to the next appropriate layer.

```text
E-Commerce Data Source
          |
          v
    Ingestion Layer
        Python
          |
          v
   Raw Data Lake Layer
        AWS S3
          |
          v
Data Quality / Validation Layer
          |
          v
Transformation / Processing Layer
     Python | PySpark
          |
          v
    Curated Data Layer
          |
          v
   Data Warehouse Layer
  Dimensional / Star Schema
          |
          v
     Data Access Layer
       Spring Boot

Apache Airflow  -> Pipeline orchestration
Docker          -> Containerisation
GitHub Actions  -> CI/CD
Makefile        -> Developer workflow automation
```

### Architectural Responsibilities

| Layer | Responsibility | Technology |
|---|---|---|
| Source | Provide the operational e-commerce dataset | Excel / source dataset |
| Ingestion | Extract source data while preserving source information | Python |
| Raw Storage | Preserve ingested source data | AWS S3 |
| Data Quality | Validate incoming data against defined quality requirements and isolate invalid records | Python / SQL |
| Processing | Standardise, transform, and prepare data | Python / PySpark |
| Curated Data | Store transformed datasets ready for loading | AWS S3 |
| Warehouse | Store structured, analysis-ready data | PostgreSQL / SQL |
| API | Provide controlled programmatic access to selected data | Java / Spring Boot |
| Orchestration | Schedule and coordinate pipeline dependencies | Apache Airflow |
| Infrastructure | Provide reproducible execution environments | Docker |
| Developer Automation | Standardise common development, testing, build, and execution commands | Makefile |
| Delivery | Automate testing and software delivery | GitHub Actions |

## Technologies

### Backend

- Java
- Spring Boot
- Spring Data
- REST APIs
- **Maven (Mvn)** — Java project build, dependency management, testing, and packaging

### Data Engineering

- Python
- PySpark
- Apache Airflow
- SQL

### Databases and Storage

- PostgreSQL
- AWS S3

### Data Warehouse

The warehouse model is being developed from the actual source dataset rather than from assumed e-commerce entities.

The current target dimensional model consists of:

- `dim_customer`
- `dim_product`
- `dim_location`
- `dim_date`
- `dim_ship_mode`
- `dim_sales_target`
- `fact_order_sales`

The central fact table preserves the source order-line grain:

> **One fact row represents one product line within an order.**

Measures include quantity, sales, profit, and discount.

Surrogate keys will be used where appropriate for warehouse dimensions, while source business identifiers and attributes will be retained where they are needed for traceability.

The model may evolve during implementation as schema design, source behaviour, and integration testing provide additional evidence.

## Core Data Engineering Concepts

The project demonstrates practical implementation of:

- Data profiling
- Data ingestion
- Data validation and data quality
- Quarantine of invalid or duplicate records
- ETL / ELT concepts
- Batch processing
- Incremental loading where supported by the source design
- Data lake architecture
- Data warehousing
- Dimensional modelling
- Data transformation
- Distributed processing
- Pipeline orchestration
- Metadata and lineage
- Idempotent processing
- Automated testing
- Containerisation
- CI/CD
- Development workflow automation

Not every concept is implemented at the same time. Each is introduced when the preceding layers provide the required foundation.

## Data Pipeline

The intended end-to-end data flow is:

```text
Source Dataset
     |
     v
Data Ingestion
     |
     v
Raw Data Lake
   AWS S3
     |
     v
Data Quality Checks
     |
     +---- invalid / duplicate records
     |             |
     |             v
     |         Quarantine
     |
     v
Transformation / Processing
   Python / PySpark
     |
     v
Curated Data
     |
     v
Data Warehouse
 PostgreSQL
     |
     v
Analysis-Ready Data
     |
     v
Analysts / Data Scientists /
Actuaries / Business Consumers
```

Apache Airflow will coordinate the dependent pipeline stages once the underlying pipeline components are independently implemented and tested.

Spring Boot provides controlled programmatic access to selected datasets and pipeline information.

Maven manages the Java/Spring Boot build lifecycle, project dependencies, automated Java tests, and packaging of the backend application.

The Makefile provides a consistent command interface for common development workflows, such as building, testing, running, and managing project services. The exact targets will be defined as implementation progresses.

## Current Implementation Progress

The project is being built incrementally. The current implemented stages include:

1. **Source data profiling** — workbook structure, columns, nulls, duplicates, keys, relationships, dates, numeric ranges, categories, grain, and location combinations were profiled.
2. **Source validation** — defined quality rules are applied before transformation.
3. **Quarantine** — identified duplicate order-line records are isolated rather than silently deleted.
4. **Transformation** — validated source data is standardised and transformed while preserving the order-line grain.
5. **JSON contract** — transformed records are being prepared as a structured interchange format between the Python data-processing layer and Java.
6. **Maven / Spring Boot foundation** — the Java backend project has been initialised and is being developed incrementally from the JSON contract.

The remaining layers are intentionally implemented in dependency order rather than being treated as a single large build.

## Engineering Objective

The primary objective is to engineer a reliable and reproducible data platform rather than perform the final business analysis.

The project therefore focuses on engineering questions such as:

- How is data extracted from the available source?
- How is raw data preserved?
- How is data quality evaluated against defined requirements?
- How are problematic records isolated for investigation?
- How is source data transformed into usable structures?
- How can historical data be retained without unnecessary full reloads when the source supports an appropriate incremental strategy?
- How should data be modelled for downstream analytical workloads?
- How are dependent pipeline stages coordinated?
- How can processing be tested and reproduced consistently?
- How can development and operational commands be standardised?
- How can downstream consumers access trusted datasets through controlled interfaces?
- How is the Java backend built, tested, and packaged consistently?

The result is an incremental, end-to-end demonstration of how operational e-commerce data can be engineered into reliable, analysis-ready data.
