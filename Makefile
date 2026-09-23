PYTHON ?= .venv/bin/python
ifeq ($(wildcard $(PYTHON)),)
PYTHON := python3
endif

.PHONY: all validate quality stats test profile transform help

all: validate

## Run data quality validation rules and produce quality stats
validate:
	@PYTHONPATH=. $(PYTHON) validation/data_validation.py

## Alias for validate
quality: validate

## Alias for validate
stats: validate

## Run the full automated test suite
test:
	@PYTHONPATH=. $(PYTHON) -m pytest

## Run source data profiling and generate profiling JSON
profile:
	@PYTHONPATH=. $(PYTHON) data_profiles.py

## Run data transformation pipeline to generate Java-ready JSON
transform:
	@PYTHONPATH=. $(PYTHON) transformation/data_transformation.py

## Display available Makefile commands
help:
	@echo "E-Commerce Data Pipeline - Available Makefile Commands:"
	@echo "  make validate   - Run data quality validation and output quality stats"
	@echo "  make quality    - Alias for make validate"
	@echo "  make stats      - Alias for make validate"
	@echo "  make test       - Run test suite with pytest"
	@echo "  make profile    - Run source data profiling"
	@echo "  make transform  - Run data transformation"
