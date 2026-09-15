"""Tests for the Python source-ingestion layer."""

from pathlib import Path

import pandas as pd
import pytest

from ingestion.data_ingestion import (
    EXPECTED_SHEETS,
    extract_workbook,
    ingest_workbook,
    validate_workbook_structure,
)


def create_workbook(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    """Create a small test workbook with the supplied sheets."""
    with pd.ExcelWriter(path) as writer:
        for sheet_name, data in sheets.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)


def test_validate_workbook_structure_accepts_expected_sheets(tmp_path: Path) -> None:
    workbook_path = tmp_path / "source.xlsx"
    create_workbook(
        workbook_path,
        {sheet: pd.DataFrame({"value": [1]}) for sheet in EXPECTED_SHEETS},
    )

    validate_workbook_structure(workbook_path)


def test_validate_workbook_structure_rejects_missing_sheet(tmp_path: Path) -> None:
    workbook_path = tmp_path / "source.xlsx"
    create_workbook(
        workbook_path,
        {
            "ListOfOrders": pd.DataFrame({"Order ID": ["A1"]}),
            "OrderBreakdown": pd.DataFrame({"Order ID": ["A1"]}),
        },
    )

    with pytest.raises(ValueError, match="SalesTargets"):
        validate_workbook_structure(workbook_path)


def test_validate_workbook_structure_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        validate_workbook_structure(tmp_path / "missing.xlsx")


def test_extract_workbook_returns_all_source_tables(tmp_path: Path) -> None:
    workbook_path = tmp_path / "source.xlsx"
    create_workbook(
        workbook_path,
        {
            "ListOfOrders": pd.DataFrame({"Order ID": ["A1", "A2"]}),
            "OrderBreakdown": pd.DataFrame({"Order ID": ["A1", "A1", "A2"]}),
            "SalesTargets": pd.DataFrame({"Category": ["Technology"]}),
        },
    )

    result = extract_workbook(workbook_path)

    assert tuple(result) == EXPECTED_SHEETS
    assert all(isinstance(data, pd.DataFrame) for data in result.values())
    assert len(result["ListOfOrders"]) == 2
    assert len(result["OrderBreakdown"]) == 3
    assert len(result["SalesTargets"]) == 1


def test_ingest_workbook_attaches_metadata_without_changing_rows(tmp_path: Path) -> None:
    workbook_path = tmp_path / "source.xlsx"
    orders = pd.DataFrame({"Order ID": ["A1"], "Sales": [100.50]})
    create_workbook(
        workbook_path,
        {
            "ListOfOrders": orders,
            "OrderBreakdown": pd.DataFrame({"Order ID": ["A1"]}),
            "SalesTargets": pd.DataFrame({"Category": ["Technology"]}),
        },
    )

    result = ingest_workbook(workbook_path)

    assert result.source_file == "source.xlsx"
    assert result.ingested_at.endswith("+00:00")
    pd.testing.assert_frame_equal(result.tables["ListOfOrders"], orders)
