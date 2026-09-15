"""Transform validated e-commerce source data into a Java-ready structure."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd


LIST_ORDER_COLUMNS = [
    "Order ID", "Order Date", "Customer Name", "City", "Country",
    "Region", "Segment", "Ship Date", "Ship Mode", "State",
]

BREAKDOWN_COLUMNS = [
    "Order ID", "Product Name", "Discount", "Sales", "Profit",
    "Quantity", "Category", "Sub-Category",
]


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Convert source column names to the JSON contract naming convention."""
    return df.rename(columns={
        "Order ID": "orderId",
        "Order Date": "orderDate",
        "Customer Name": "customerName",
        "City": "city",
        "Country": "country",
        "Region": "region",
        "Segment": "segment",
        "Ship Date": "shipDate",
        "Ship Mode": "shipMode",
        "State": "state",
        "Product Name": "productName",
        "Discount": "discount",
        "Sales": "sales",
        "Profit": "profit",
        "Quantity": "quantity",
        "Category": "category",
        "Sub-Category": "subCategory",
    })


def standardize_types(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize dates and numeric fields without changing business values."""
    result = df.copy()

    for column in ("orderDate", "shipDate"):
        if column in result.columns:
            result[column] = pd.to_datetime(result[column]).dt.strftime("%Y-%m-%d")

    for column in ("quantity",):
        if column in result.columns:
            result[column] = result[column].astype(int)

    for column in ("discount", "sales", "profit"):
        if column in result.columns:
            result[column] = result[column].astype(float)

    return result


def combine_order_data(
    orders: pd.DataFrame, order_lines: pd.DataFrame
) -> pd.DataFrame:
    """Join order-level attributes to order-line records using Order ID."""
    orders = standardize_column_names(orders)
    order_lines = standardize_column_names(order_lines)

    combined = order_lines.merge(
        orders,
        on="orderId",
        how="inner",
        validate="many_to_one",
    )

    return standardize_types(combined)


def transform_orders(
    orders: pd.DataFrame, order_lines: pd.DataFrame
) -> list[dict[str, Any]]:
    """Create one JSON-ready record per product line within an order."""
    combined = combine_order_data(orders, order_lines)

    records: list[dict[str, Any]] = []
    for row in combined.to_dict(orient="records"):
        records.append({
            "orderId": row["orderId"],
            "orderDate": row["orderDate"],
            "customer": {
                "name": row["customerName"],
                "segment": row["segment"],
            },
            "location": {
                "city": row["city"],
                "state": row["state"],
                "country": row["country"],
                "region": row["region"],
            },
            "shipping": {
                "shipDate": row["shipDate"],
                "shipMode": row["shipMode"],
            },
            "orderLine": {
                "productName": row["productName"],
                "category": row["category"],
                "subCategory": row["subCategory"],
                "quantity": row["quantity"],
                "discount": row["discount"],
                "sales": row["sales"],
                "profit": row["profit"],
            },
        })

    return records


def serialize_orders(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return JSON-compatible Python records for downstream serialization."""
    return records
