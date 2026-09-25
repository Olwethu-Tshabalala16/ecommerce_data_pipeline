PYTHON ?= .venv/bin/python
ifeq ($(wildcard $(PYTHON)),)
PYTHON := python3
endif

.PHONY: all validate quality stats test java-test java-package docker-build up down logs help

all: test java-test

## Run data quality validation rules and produce quality stats
validate:
	@PYTHONPATH=. $(PYTHON) validation/data_validation.py

## Alias for validate
quality: validate

## Alias for validate
stats: validate

## Run the Python automated test suite
test:
	@PYTHONPATH=. $(PYTHON) -m pytest

## Run Java/Spring Boot tests
java-test:
	@mvn -q test

## Build the Spring Boot application without running tests
java-package:
	@mvn -q -DskipTests package

## Build Docker images
docker-build:
	@docker compose build

## Start the local containerized stack
up:
	@docker compose up --build -d

## Stop the local containerized stack
down:
	@docker compose down

## Follow container logs
logs:
	@docker compose logs -f

## Run source data profiling and generate profiling JSON
profile:
	@PYTHONPATH=. $(PYTHON) data_profiles.py

## Run the PySpark transformation pipeline
transform:
	@PYTHONPATH=. $(PYTHON) transformation/pyspark_transformation.py

## Display available Makefile commands
help:
	@echo "E-Commerce Data Pipeline - Available Makefile Commands:"
	@echo "  make test         - Run Python test suite"
	@echo "  make java-test    - Run Java/Spring Boot tests"
	@echo "  make java-package - Package the Spring Boot API"
	@echo "  make docker-build - Build Docker images"
	@echo "  make up           - Start PostgreSQL, API, and Airflow"
	@echo "  make down         - Stop the containerized stack"
	@echo "  make logs         - Follow container logs"
	@echo "  make validate     - Run data quality validation"
	@echo "  make profile      - Run source data profiling"
	@echo "  make transform    - Run PySpark transformation"
