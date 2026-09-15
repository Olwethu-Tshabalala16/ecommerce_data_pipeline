"""
Validation utilities for the AmazingMart e-commerce source data.

Validation identifies records that violate defined data-quality rules.
It does not transform the source data or remove unusual but valid values.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = {
    "ListOfOrders": {
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
    },
    "OrderBreakdown": {
        "Order ID",
        "Product Name",
        "Discount",
        "Sales",
        "Profit",
        "Quantity",
        "Category",
        "Sub-Category",
    },
    "SalesTargets": {
        "Month of Order Date",
        "Category",
        "Target",
    },
}


def validate_required_columns(
    data: pd.DataFrame,
    table_name: str,
) -> list[str]:
    """Return required columns that are missing from a source table."""
    required = REQUIRED_COLUMNS[table_name]
    return sorted(required - set(data.columns))


def validate_required_values(
    data: pd.DataFrame,
    columns: Iterable[str],
) -> pd.DataFrame:
    """Return rows containing null values in required columns."""
    columns = list(columns)
    return data[data[columns].isna().any(axis=1)].copy()


def validate_unique_key(
    data: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """Return rows that violate uniqueness or completeness of a key."""
    invalid = data[column].isna() | data[column].duplicated(keep=False)
    return data[invalid].copy()


def validate_dates(
    data: pd.DataFrame,
    date_columns: Iterable[str],
) -> pd.DataFrame:
    """Return rows containing values that cannot be interpreted as dates."""
    date_columns = list(date_columns)
    invalid = pd.Series(False, index=data.index)

    for column in date_columns:
        invalid |= pd.to_datetime(data[column], errors="coerce").isna()

    return data[invalid].copy()


def validate_shipping_dates(data: pd.DataFrame) -> pd.DataFrame:
    """Return rows where shipping occurs before the order date."""
    order_dates = pd.to_datetime(data["Order Date"], errors="coerce")
    ship_dates = pd.to_datetime(data["Ship Date"], errors="coerce")

    invalid = ship_dates < order_dates
    return data[invalid.fillna(False)].copy()


def validate_order_references(
    orders: pd.DataFrame,
    order_breakdown: pd.DataFrame,
) -> pd.DataFrame:
    """Return order-line rows whose Order ID does not exist in the orders table."""
    valid_order_ids = set(orders["Order ID"].dropna())
    invalid = ~order_breakdown["Order ID"].isin(valid_order_ids)
    return order_breakdown[invalid].copy()


def validate_positive_quantity(data: pd.DataFrame) -> pd.DataFrame:
    """Return order-line rows with zero or negative quantity."""
    invalid = pd.to_numeric(data["Quantity"], errors="coerce").le(0)
    invalid |= pd.to_numeric(data["Quantity"], errors="coerce").isna()
    return data[invalid].copy()


def validate_discount(data: pd.DataFrame) -> pd.DataFrame:
    """Return order-line rows with discounts outside the inclusive 0-1 range."""
    discount = pd.to_numeric(data["Discount"], errors="coerce")
    invalid = discount.isna() | discount.lt(0) | discount.gt(1)
    return data[invalid].copy()


def validate_sales(data: pd.DataFrame) -> pd.DataFrame:
    """Return order-line rows with invalid sales values."""
    sales = pd.to_numeric(data["Sales"], errors="coerce")
    invalid = sales.isna() | sales.lt(0)
    return data[invalid].copy()


def validate_numeric_column(
    data: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """Return rows where a required numeric column cannot be parsed as numeric."""
    values = pd.to_numeric(data[column], errors="coerce")
    return data[values.isna()].copy()


def validate_target_combinations(data: pd.DataFrame) -> pd.DataFrame:
    """Return duplicate month/category combinations from sales targets."""
    duplicates = data.duplicated(
        subset=["Month of Order Date", "Category"],
        keep=False,
    )
    return data[duplicates].copy()


def validate_source_tables(
    orders: pd.DataFrame,
    order_breakdown: pd.DataFrame,
    sales_targets: pd.DataFrame,
) -> dict[str, pd.DataFrame | list[str]]:
    """Run the defined validation rules and return failures by rule."""
    return {
        "orders_missing_columns": validate_required_columns(
            orders,
            "ListOfOrders",
        ),
        "orders_missing_values": validate_required_values(
            orders,
            REQUIRED_COLUMNS["ListOfOrders"],
        ),
        "orders_invalid_keys": validate_unique_key(orders, "Order ID"),
        "orders_invalid_dates": validate_dates(
            orders,
            ["Order Date", "Ship Date"],
        ),
        "orders_invalid_shipping_dates": validate_shipping_dates(orders),
        "breakdown_missing_columns": validate_required_columns(
            order_breakdown,
            "OrderBreakdown",
        ),
        "breakdown_missing_values": validate_required_values(
            order_breakdown,
            REQUIRED_COLUMNS["OrderBreakdown"],
        ),
        "breakdown_invalid_order_references": validate_order_references(
            orders,
            order_breakdown,
        ),
        "breakdown_invalid_quantity": validate_positive_quantity(order_breakdown),
        "breakdown_invalid_discount": validate_discount(order_breakdown),
        "breakdown_invalid_sales": validate_sales(order_breakdown),
        "targets_missing_columns": validate_required_columns(
            sales_targets,
            "SalesTargets",
        ),
        "targets_missing_values": validate_required_values(
            sales_targets,
            REQUIRED_COLUMNS["SalesTargets"],
        ),
        "targets_invalid_dates": validate_dates(
            sales_targets,
            ["Month of Order Date"],
        ),
        "targets_invalid_target": validate_numeric_column(sales_targets, "Target"),
        "targets_duplicate_combinations": validate_target_combinations(sales_targets),
    }
