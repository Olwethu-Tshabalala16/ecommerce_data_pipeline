"""Tests for the Python source-ingestion layer."""

from pathlib import Path

import pandas as pd
import pytest

from ingestion.data_ingestion import (
    EXPECTED_COLUMNS,
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


def valid_test_sheets() -> dict[str, pd.DataFrame]:
    """Create minimal tables matching the source workbook contract."""
    return {
        sheet_name: pd.DataFrame({column: [1] for column in columns})
        for sheet_name, columns in EXPECTED_COLUMNS.items()
    }


def test_validate_workbook_structure_accepts_expected_sheets_and_columns(tmp_path: Path) -> None:
    workbook_path = tmp_path / "source.xlsx"
    create_workbook(workbook_path, valid_test_sheets())

    validate_workbook_structure(workbook_path)


def test_validate_workbook_structure_rejects_missing_sheet(tmp_path: Path) -> None:
    workbook_path = tmp_path / "source.xlsx"
    sheets = valid_test_sheets()
    sheets.pop("SalesTargets")
    create_workbook(workbook_path, sheets)

    with pytest.raises(ValueError, match="SalesTargets"):
        validate_workbook_structure(workbook_path)


def test_validate_workbook_structure_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        validate_workbook_structure(tmp_path / "missing.xlsx")


def test_validate_workbook_structure_rejects_missing_required_column(tmp_path: Path) -> None:
    workbook_path = tmp_path / "source.xlsx"
    sheets = valid_test_sheets()
    sheets["OrderBreakdown"] = sheets["OrderBreakdown"].drop(columns=["Profit"])
    create_workbook(workbook_path, sheets)

    with pytest.raises(ValueError, match="Profit"):
        validate_workbook_structure(workbook_path)


def test_extract_workbook_returns_all_source_tables(tmp_path: Path) -> None:
    workbook_path = tmp_path / "source.xlsx"
    sheets = valid_test_sheets()
    sheets["ListOfOrders"] = pd.DataFrame(
        {column: [1, 2] for column in EXPECTED_COLUMNS["ListOfOrders"]}
    )
    sheets["OrderBreakdown"] = pd.DataFrame(
        {column: [1, 2, 3] for column in EXPECTED_COLUMNS["OrderBreakdown"]}
    )
    create_workbook(workbook_path, sheets)

    result = extract_workbook(workbook_path)

    assert tuple(result) == EXPECTED_SHEETS
    assert all(isinstance(data, pd.DataFrame) for data in result.values())
    assert len(result["ListOfOrders"]) == 2
    assert len(result["OrderBreakdown"]) == 3
    assert len(result["SalesTargets"]) == 1


def test_ingest_workbook_attaches_metadata_without_changing_rows(tmp_path: Path) -> None:
    workbook_path = tmp_path / "source.xlsx"
    sheets = valid_test_sheets()
    orders = pd.DataFrame(
        {column: [1] for column in EXPECTED_COLUMNS["ListOfOrders"]}
    )
    sheets["ListOfOrders"] = orders
    create_workbook(workbook_path, sheets)

    result = ingest_workbook(workbook_path)

    assert result.source_file == "source.xlsx"
    assert result.ingested_at.endswith("+00:00")
    pd.testing.assert_frame_equal(result.tables["ListOfOrders"], orders)
