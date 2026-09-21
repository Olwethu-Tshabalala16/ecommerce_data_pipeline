"""
Data profiling utilities for the AmazingMart e-commerce dataset.

This module is intentionally focused on profiling rather than transformation.
The functions answer questions about schema, volume, keys, missing data,
duplicates, relationships, ranges, and categorical values.
"""

from contextlib import redirect_stdout
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd


WORKBOOK_PATH = Path("(ecommerce)P1-AmazingMartEU2.xlsx")
PROFILE_OUTPUT_PATH = Path("profiling/output/data_profile.json")


def load_workbook(workbook_path: Path) -> dict[str, pd.DataFrame]:
    """Load all source sheets into DataFrames."""
    workbook = pd.ExcelFile(workbook_path)

    return {
        sheet_name: pd.read_excel(workbook, sheet_name=sheet_name)
        for sheet_name in workbook.sheet_names
    }


def profile_shape(data: pd.DataFrame, table_name: str) -> None:
    """Report the number of rows and columns in a source table."""
    rows, columns = data.shape

    print(f"\n=== {table_name}: SHAPE ===")
    print(f"Rows: {rows:,}")
    print(f"Columns: {columns}")


def profile_columns(data: pd.DataFrame, table_name: str) -> None:
    """Report source column names and pandas data types."""
    print(f"\n=== {table_name}: COLUMNS / DATA TYPES ===")

    for column, data_type in data.dtypes.items():
        print(f"{column}: {data_type}")


def profile_missing_values(data: pd.DataFrame, table_name: str) -> None:
    """Report missing values for every column."""
    missing = data.isna().sum()

    print(f"\n=== {table_name}: MISSING VALUES ===")

    for column, count in missing.items():
        print(f"{column}: {count:,}")


def profile_duplicates(data: pd.DataFrame, table_name: str) -> None:
    """Report exact duplicate rows."""
    duplicate_count = data.duplicated().sum()

    print(f"\n=== {table_name}: DUPLICATES ===")
    print(f"Exact duplicate rows: {duplicate_count:,}")

    if duplicate_count:
        print("\nDuplicate records:")
        print(data[data.duplicated(keep=False)].to_string(index=False))


def profile_unique_values(
    data: pd.DataFrame,
    columns: list[str],
    table_name: str,
) -> None:
    """Report unique-value counts for selected columns."""
    print(f"\n=== {table_name}: UNIQUE VALUES ===")

    for column in columns:
        print(f"{column}: {data[column].nunique(dropna=True):,}")


def profile_key(
    data: pd.DataFrame,
    column: str,
    table_name: str,
) -> None:
    """Check whether a candidate key is unique and complete."""
    unique_count = data[column].nunique(dropna=True)
    row_count = len(data)
    null_count = data[column].isna().sum()

    print(f"\n=== {table_name}: KEY PROFILE ===")
    print(f"Candidate key: {column}")
    print(f"Rows: {row_count:,}")
    print(f"Unique values: {unique_count:,}")
    print(f"Null values: {null_count:,}")
    print(f"Unique key: {unique_count == row_count and null_count == 0}")


def profile_date_column(
    data: pd.DataFrame,
    column: str,
    table_name: str,
) -> None:
    """Report the valid date range for a date column."""
    dates = pd.to_datetime(data[column], errors="coerce")

    print(f"\n=== {table_name}: DATE PROFILE ({column}) ===")
    print(f"Invalid dates: {dates.isna().sum():,}")

    if dates.notna().any():
        print(f"Earliest date: {dates.min()}")
        print(f"Latest date: {dates.max()}")


def profile_numeric_column(
    data: pd.DataFrame,
    column: str,
    table_name: str,
) -> None:
    """Report basic statistics for a numeric column."""
    values = pd.to_numeric(data[column], errors="coerce")

    print(f"\n=== {table_name}: NUMERIC PROFILE ({column}) ===")
    print(f"Invalid numeric values: {values.isna().sum():,}")

    if values.notna().any():
        print(f"Minimum: {values.min()}")
        print(f"Maximum: {values.max()}")
        print(f"Mean: {values.mean():.2f}")


def profile_categories(
    data: pd.DataFrame,
    column: str,
    table_name: str,
) -> None:
    """Report the distinct categorical values in a column."""
    values = data[column].dropna().unique()

    print(f"\n=== {table_name}: CATEGORIES ({column}) ===")
    print(f"Distinct values: {len(values):,}")

    for value in sorted(values, key=str):
        print(value)


def profile_relationship(
    parent: pd.DataFrame,
    child: pd.DataFrame,
    key: str,
    parent_name: str,
    child_name: str,
) -> None:
    """Check whether child records have matching parent keys."""
    parent_keys = set(parent[key].dropna())
    child_keys = set(child[key].dropna())

    orphan_keys = child_keys - parent_keys

    print("\n=== RELATIONSHIP PROFILE ===")
    print(f"{child_name}.{key} -> {parent_name}.{key}")
    print(f"Parent unique keys: {len(parent_keys):,}")
    print(f"Child unique keys: {len(child_keys):,}")
    print(f"Orphan child keys: {len(orphan_keys):,}")

    if orphan_keys:
        print("Sample orphan keys:", list(orphan_keys)[:10])


def profile_order_grain(
    orders: pd.DataFrame,
    order_breakdown: pd.DataFrame,
) -> None:
    """Determine the relationship between orders and order-line records."""
    order_counts = order_breakdown.groupby("Order ID").size()

    print("\n=== ORDER GRAIN PROFILE ===")
    print(f"Orders: {len(orders):,}")
    print(f"Order breakdown rows: {len(order_breakdown):,}")
    print(f"Unique order IDs in breakdown: {order_breakdown['Order ID'].nunique():,}")
    print(f"Minimum lines per order: {order_counts.min()}")
    print(f"Maximum lines per order: {order_counts.max()}")
    print(f"Average lines per order: {order_counts.mean():.2f}")


def profile_location_combinations(
    data: pd.DataFrame,
    columns: list[str],
) -> None:
    """Find values that map to more than one geographic combination."""
    grouped = data.groupby(columns[:-1])[columns[-1]].nunique()
    ambiguous = grouped[grouped > 1]

    print("\n=== LOCATION CONSISTENCY PROFILE ===")
    print(f"Ambiguous {columns[:-1]} combinations: {len(ambiguous):,}")

    if len(ambiguous):
        print(ambiguous)


def profile_sales_targets(data: pd.DataFrame) -> None:
    """Profile the month/category target table."""
    data["Month of Order Date"] = pd.to_datetime(
        data["Month of Order Date"],
        errors="coerce",
    )

    combinations = data[["Month of Order Date", "Category"]].duplicated().sum()

    print("\n=== SALES TARGET PROFILE ===")
    print(f"Rows: {len(data):,}")
    print(f"Unique months: {data['Month of Order Date'].nunique():,}")
    print(f"Unique categories: {data['Category'].nunique():,}")
    print(f"Duplicate month/category combinations: {combinations:,}")
    print(f"Earliest month: {data['Month of Order Date'].min()}")
    print(f"Latest month: {data['Month of Order Date'].max()}")


def run_profile(workbook_path: Path) -> None:
    """Run the complete source-data profiling process."""
    tables = load_workbook(workbook_path)

    orders = tables["ListOfOrders"]
    order_breakdown = tables["OrderBreakdown"]
    sales_targets = tables["SalesTargets"]

    profile_shape(orders, "ListOfOrders")
    profile_columns(orders, "ListOfOrders")
    profile_missing_values(orders, "ListOfOrders")
    profile_duplicates(orders, "ListOfOrders")
    profile_key(orders, "Order ID", "ListOfOrders")
    profile_unique_values(
        orders,
        ["Customer Name", "City", "Country", "Region", "Segment", "Ship Mode", "State"],
        "ListOfOrders",
    )
    profile_date_column(orders, "Order Date", "ListOfOrders")
    profile_date_column(orders, "Ship Date", "ListOfOrders")

    profile_shape(order_breakdown, "OrderBreakdown")
    profile_columns(order_breakdown, "OrderBreakdown")
    profile_missing_values(order_breakdown, "OrderBreakdown")
    profile_duplicates(order_breakdown, "OrderBreakdown")
    profile_unique_values(
        order_breakdown,
        ["Order ID", "Product Name", "Category", "Sub-Category"],
        "OrderBreakdown",
    )
    profile_numeric_column(order_breakdown, "Quantity", "OrderBreakdown")
    profile_numeric_column(order_breakdown, "Discount", "OrderBreakdown")
    profile_numeric_column(order_breakdown, "Sales", "OrderBreakdown")
    profile_numeric_column(order_breakdown, "Profit", "OrderBreakdown")
    profile_categories(order_breakdown, "Category", "OrderBreakdown")
    profile_categories(order_breakdown, "Sub-Category", "OrderBreakdown")

    profile_shape(sales_targets, "SalesTargets")
    profile_columns(sales_targets, "SalesTargets")
    profile_missing_values(sales_targets, "SalesTargets")
    profile_duplicates(sales_targets, "SalesTargets")
    profile_sales_targets(sales_targets)

    profile_relationship(
        orders,
        order_breakdown,
        "Order ID",
        "ListOfOrders",
        "OrderBreakdown",
    )

    profile_order_grain(orders, order_breakdown)

    profile_location_combinations(
        orders,
        ["City", "Country", "State"],
    )


def generate_profile_json(
    workbook_path: Path,
    output_path: Path = PROFILE_OUTPUT_PATH,
) -> Path:
    """Generate or update a JSON artifact containing the profiling report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from io import StringIO

    report = StringIO()

    with redirect_stdout(report):
        run_profile(workbook_path)

    profile = {
        "source_file": workbook_path.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile_report": report.getvalue(),
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(profile, file, indent=2)

    return output_path


if __name__ == "__main__":
    generate_profile_json(WORKBOOK_PATH)
