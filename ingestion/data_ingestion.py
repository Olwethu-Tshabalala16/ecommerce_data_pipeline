"""
Source ingestion utilities for the AmazingMart e-commerce workbook.

Ingestion is responsible for extracting the source datasets without applying
business transformations. Data-quality validation and transformation are
separate pipeline stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

EXPECTED_SHEETS = ("ListOfOrders", "OrderBreakdown", "SalesTargets")

EXPECTED_COLUMNS = {
    "ListOfOrders": (
        "Order ID",
        "Order Date",
        "Customer Name",
        "City",
        "Country",
        "Region",
        "Segment",
        "Ship Date",
        "Ship Mode",
        "State",
    ),
    "OrderBreakdown": (
        "Order ID",
        "Product Name",
        "Discount",
        "Sales",
        "Profit",
        "Quantity",
        "Category",
        "Sub-Category",
    ),
    "SalesTargets": (
        "Month of Order Date",
        "Category",
        "Target",
    ),
}


@dataclass(frozen=True)
class IngestionResult:
    """Container for extracted source tables and ingestion metadata."""

    tables: dict[str, pd.DataFrame]
    source_file: str
    ingested_at: str


def validate_workbook_structure(workbook_path: Path) -> None:
    """Ensure the source workbook has the required sheets and columns."""
    if not workbook_path.is_file():
        raise FileNotFoundError(f"Source workbook not found: {workbook_path}")

    workbook = pd.ExcelFile(workbook_path)
    actual_sheets = tuple(workbook.sheet_names)

    missing_sheets = [sheet for sheet in EXPECTED_SHEETS if sheet not in actual_sheets]
    if missing_sheets:
        raise ValueError(f"Missing required source sheets: {missing_sheets}")

    for sheet_name in EXPECTED_SHEETS:
        columns = tuple(pd.read_excel(workbook, sheet_name=sheet_name, nrows=0).columns)
        missing_columns = [
            column for column in EXPECTED_COLUMNS[sheet_name] if column not in columns
        ]
        if missing_columns:
            raise ValueError(
                f"Missing required columns in {sheet_name}: {missing_columns}"
            )


def extract_workbook(workbook_path: Path) -> dict[str, pd.DataFrame]:
    """Extract the expected source sheets into DataFrames."""
    validate_workbook_structure(workbook_path)
    workbook = pd.ExcelFile(workbook_path)

    return {
        sheet_name: pd.read_excel(workbook, sheet_name=sheet_name)
        for sheet_name in EXPECTED_SHEETS
    }


def ingest_workbook(workbook_path: Path) -> IngestionResult:
    """Extract the source workbook and attach ingestion metadata."""
    tables = extract_workbook(workbook_path)
    ingested_at = datetime.now(timezone.utc).isoformat()

    return IngestionResult(
        tables=tables,
        source_file=workbook_path.name,
        ingested_at=ingested_at,
    )
