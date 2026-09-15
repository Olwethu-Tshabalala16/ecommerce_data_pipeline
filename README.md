# E-Commerce Data Pipeline

## Problem Statement

E-commerce platforms generate large amounts of operational data from customers, products, orders, payments, and inventory. Although this data is valuable, raw operational data is not automatically suitable for reliable downstream analysis.

Real-world data can contain missing values, duplicate records, invalid values, inconsistent formats, broken relationships between entities, and other quality issues. Data also needs to be stored in a way that preserves raw information while making processed data efficient and consistent for downstream consumers.

This project addresses that problem by engineering an end-to-end data platform that ingests e-commerce data, preserves raw data, validates data quality, transforms data into structured datasets, loads analysis-ready data into a warehouse, orchestrates the pipeline, and exposes selected data and pipeline information through an API.

The project focuses on **Data Engineering rather than final business analysis**. The Data Engineer is responsible for building the infrastructure and pipelines that make reliable downstream analysis possible. Data Analysts, Data Scientists, Actuaries, and business stakeholders can then use the resulting datasets to answer business questions and make decisions.

## Architecture

This project follows a **Layered Architecture**, where each layer has a defined responsibility and passes data or services to the next appropriate layer.

```text
E-Commerce Data Sources
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
```

### Architectural Responsibilities

| Layer | Responsibility | Technology |
|---|---|---|
| Source | Generate and maintain operational e-commerce data | PostgreSQL |
| Ingestion | Extract data from source systems | Python |
| Raw Storage | Preserve ingested source data | AWS S3 |
| Data Quality | Validate incoming data against defined quality requirements | Python / SQL |
| Processing | Clean, transform, and prepare data | Python / PySpark |
| Curated Data | Store transformed datasets ready for loading | AWS S3 |
| Warehouse | Store structured, analysis-ready data | PostgreSQL / SQL |
| API | Provide controlled programmatic access to data | Java / Spring Boot |
| Orchestration | Schedule and coordinate pipeline dependencies | Apache Airflow |
| Infrastructure | Provide reproducible execution environments | Docker |
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

The initial dimensional warehouse model consists of:

- `dim_customer`
- `dim_product`
- `dim_date`
- `fact_orders`
- `fact_payments`

### Infrastructure and DevOps

- Docker
- Git
- GitHub
- GitHub Actions

### Testing

- JUnit
- Pytest

## Core Data Engineering Concepts

The project demonstrates practical implementation of:

- Data ingestion
- Data validation and data quality
- ETL / ELT concepts
- Batch processing
- Incremental loading
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

## Data Pipeline

The intended data flow is:

```text
Operational E-Commerce Data
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
            v
 Transformation / Processing
       Python / PySpark
            |
            v
       Curated Data
            |
            v
      Data Warehouse
            |
            v
    Analysis-Ready Data
            |
            v
 Analysts / Data Scientists /
 Actuaries / Business Consumers
```

Apache Airflow coordinates the dependent pipeline stages, while Spring Boot provides controlled programmatic access to selected datasets and pipeline information.

Maven manages the Java/Spring Boot build lifecycle, project dependencies, automated Java tests, and packaging of the backend application.

## Engineering Objective

The primary objective is to engineer a reliable and reproducible data platform rather than perform the final business analysis.

The project therefore focuses on engineering questions such as:

- How is data extracted from operational systems?
- How is raw data preserved?
- How is data quality evaluated against defined requirements?
- How is source data transformed into usable structures?
- How can historical data be retained while avoiding unnecessary full reloads?
- How should data be modelled for downstream analytical workloads?
- How are dependent pipeline stages coordinated?
- How can processing be tested and reproduced consistently?
- How can downstream consumers access trusted datasets through controlled interfaces?
- How is the Java backend built, tested, and packaged consistently?

The result is an end-to-end demonstration of how operational e-commerce data can be engineered into reliable, analysis-ready data.
