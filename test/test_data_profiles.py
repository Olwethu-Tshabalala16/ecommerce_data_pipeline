"""Tests for the source-data profiling functions."""

import json
from pathlib import Path

import pandas as pd

from data_profiles import (
    generate_profile_json,
    load_workbook,
    profile_categories,
    profile_columns,
    profile_date_column,
    profile_duplicates,
    profile_key,
    profile_location_combinations,
    profile_missing_values,
    profile_numeric_column,
    profile_order_grain,
    profile_relationship,
    profile_sales_targets,
    profile_shape,
    profile_unique_values,
)


def test_load_workbook(tmp_path: Path) -> None:
    """The workbook loader returns every sheet as a DataFrame."""
    workbook_path = tmp_path / "test.xlsx"

    orders = pd.DataFrame({"Order ID": ["A1", "A2"]})
    breakdown = pd.DataFrame({"Order ID": ["A1", "A1", "A2"]})
    targets = pd.DataFrame({"Category": ["Technology"]})

    with pd.ExcelWriter(workbook_path) as writer:
        orders.to_excel(writer, sheet_name="ListOfOrders", index=False)
        breakdown.to_excel(writer, sheet_name="OrderBreakdown", index=False)
        targets.to_excel(writer, sheet_name="SalesTargets", index=False)

    result = load_workbook(workbook_path)

    assert set(result) == {"ListOfOrders", "OrderBreakdown", "SalesTargets"}
    assert all(isinstance(data, pd.DataFrame) for data in result.values())
    assert len(result["ListOfOrders"]) == 2
    assert len(result["OrderBreakdown"]) == 3
    assert len(result["SalesTargets"]) == 1


def test_profile_shape(capsys) -> None:
    data = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

    profile_shape(data, "TestTable")

    output = capsys.readouterr().out
    assert "Rows: 2" in output
    assert "Columns: 2" in output


def test_profile_columns(capsys) -> None:
    data = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})

    profile_columns(data, "TestTable")

    output = capsys.readouterr().out
    assert "A:" in output
    assert "B:" in output


def test_profile_missing_values(capsys) -> None:
    data = pd.DataFrame({"A": [1, None], "B": ["x", "y"]})

    profile_missing_values(data, "TestTable")

    output = capsys.readouterr().out
    assert "A: 1" in output
    assert "B: 0" in output


def test_profile_duplicates(capsys) -> None:
    data = pd.DataFrame({"A": [1, 1, 2]})

    profile_duplicates(data, "TestTable")

    output = capsys.readouterr().out
    assert "Exact duplicate rows: 1" in output
    assert "Duplicate records:" in output


def test_profile_unique_values(capsys) -> None:
    data = pd.DataFrame({"Category": ["A", "A", "B", None]})

    profile_unique_values(data, ["Category"], "TestTable")

    output = capsys.readouterr().out
    assert "Category: 2" in output


def test_profile_key_identifies_unique_complete_key(capsys) -> None:
    data = pd.DataFrame({"Order ID": ["A1", "A2", "A3"]})

    profile_key(data, "Order ID", "TestTable")

    output = capsys.readouterr().out
    assert "Unique values: 3" in output
    assert "Null values: 0" in output
    assert "Unique key: True" in output


def test_profile_key_rejects_duplicate_key(capsys) -> None:
    data = pd.DataFrame({"Order ID": ["A1", "A1", "A2"]})

    profile_key(data, "Order ID", "TestTable")

    output = capsys.readouterr().out
    assert "Unique key: False" in output


def test_profile_date_column_reports_invalid_dates(capsys) -> None:
    data = pd.DataFrame({"Order Date": ["2024-01-01", "not-a-date"]})

    profile_date_column(data, "Order Date", "TestTable")

    output = capsys.readouterr().out
    assert "Invalid dates: 1" in output
    assert "Earliest date:" in output
    assert "Latest date:" in output


def test_profile_numeric_column_reports_invalid_values(capsys) -> None:
    data = pd.DataFrame({"Sales": [100, 200, "invalid"]})

    profile_numeric_column(data, "Sales", "TestTable")

    output = capsys.readouterr().out
    assert "Invalid numeric values: 1" in output
    assert "Minimum: 100" in output
    assert "Maximum: 200" in output
    assert "Mean: 150.00" in output


def test_profile_categories_lists_distinct_values(capsys) -> None:
    data = pd.DataFrame({"Category": ["Technology", "Furniture", "Technology"]})

    profile_categories(data, "Category", "TestTable")

    output = capsys.readouterr().out
    assert "Distinct values: 2" in output
    assert "Furniture" in output
    assert "Technology" in output


def test_profile_relationship_detects_orphans(capsys) -> None:
    parent = pd.DataFrame({"Order ID": ["A1", "A2"]})
    child = pd.DataFrame({"Order ID": ["A1", "A3"]})

    profile_relationship(parent, child, "Order ID", "Orders", "OrderLines")

    output = capsys.readouterr().out
    assert "Orphan child keys: 1" in output
    assert "A3" in output


def test_profile_order_grain_reports_line_range(capsys) -> None:
    orders = pd.DataFrame({"Order ID": ["A1", "A2"]})
    breakdown = pd.DataFrame({"Order ID": ["A1", "A1", "A2"]})

    profile_order_grain(orders, breakdown)

    output = capsys.readouterr().out
    assert "Orders: 2" in output
    assert "Order breakdown rows: 3" in output
    assert "Unique order IDs in breakdown: 2" in output
    assert "Minimum lines per order: 1" in output
    assert "Maximum lines per order: 2" in output
    assert "Average lines per order: 1.50" in output


def test_profile_location_combinations_detects_ambiguity(capsys) -> None:
    data = pd.DataFrame(
        {
            "City": ["Halle", "Halle", "Berlin"],
            "Country": ["Germany", "Germany", "Germany"],
            "State": ["Saxony-Anhalt", "North Rhine-Westphalia", "Berlin"],
        }
    )

    profile_location_combinations(data, ["City", "Country", "State"])

    output = capsys.readouterr().out
    assert "Ambiguous ['City', 'Country'] combinations: 1" in output
    assert "Halle" in output


def test_profile_sales_targets_detects_duplicate_month_category(capsys) -> None:
    data = pd.DataFrame(
        {
            "Month of Order Date": ["2024-01-01", "2024-01-01", "2024-02-01"],
            "Category": ["Technology", "Technology", "Furniture"],
            "Target": [1000, 1000, 1200],
        }
    )

    profile_sales_targets(data)

    output = capsys.readouterr().out
    assert "Rows: 3" in output
    assert "Unique months: 2" in output
    assert "Unique categories: 2" in output
    assert "Duplicate month/category combinations: 1" in output
    assert "Earliest month:" in output
    assert "Latest month:" in output


def test_generate_profile_json(tmp_path: Path) -> None:
    workbook_path = tmp_path / "test.xlsx"
    output_path = tmp_path / "profiling" / "output" / "data_profile.json"

    orders = pd.DataFrame({
        "Order ID": ["A1"],
        "Order Date": ["2024-01-01"],
        "Ship Date": ["2024-01-03"],
        "Customer Name": ["Alice"],
        "City": ["Berlin"],
        "Country": ["Germany"],
        "Region": ["Central"],
        "Segment": ["Consumer"],
        "Ship Mode": ["Economy"],
        "State": ["Berlin"],
    })
    breakdown = pd.DataFrame({
        "Order ID": ["A1"],
        "Product Name": ["Item 1"],
        "Category": ["Technology"],
        "Sub-Category": ["Phones"],
        "Quantity": [2],
        "Discount": [0.1],
        "Sales": [100],
        "Profit": [20],
    })
    targets = pd.DataFrame({
        "Month of Order Date": ["2024-01-01"],
        "Category": ["Technology"],
        "Target": [1000],
    })

    with pd.ExcelWriter(workbook_path) as writer:
        orders.to_excel(writer, sheet_name="ListOfOrders", index=False)
        breakdown.to_excel(writer, sheet_name="OrderBreakdown", index=False)
        targets.to_excel(writer, sheet_name="SalesTargets", index=False)

    result_path = generate_profile_json(workbook_path, output_path)

    assert result_path == output_path
    assert output_path.exists()

    with output_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["source_file"] == "test.xlsx"
    assert "generated_at" in data
    assert "ListOfOrders: SHAPE" in data["profile_report"]

