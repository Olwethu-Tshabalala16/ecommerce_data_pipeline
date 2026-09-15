"""Transform validated e-commerce source data into a Java-ready JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


OUTPUT_PATH = Path("transformation/output/transformed_orders.json")


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

    if "quantity" in result.columns:
        result["quantity"] = result["quantity"].astype(int)

    for column in ("discount", "sales", "profit"):
        if column in result.columns:
            result[column] = result[column].astype(float)

    return result


def combine_order_data(
    orders: pd.DataFrame, order_lines: pd.DataFrame
) -> pd.DataFrame:
    """Join order-level attributes to valid order-line records using Order ID."""
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
    """Create one JSON-ready record per valid product line within an order."""
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


def write_json(records: list[dict[str, Any]], output_path: Path = OUTPUT_PATH) -> Path:
    """Serialize transformed records to a UTF-8 JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)
    return output_path


def generate_json(
    workbook_path: Path,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Read the source workbook, quarantine exact duplicate lines, then transform valid data."""
    orders = pd.read_excel(workbook_path, sheet_name="ListOfOrders")
    order_lines = pd.read_excel(workbook_path, sheet_name="OrderBreakdown")

    # Exact duplicate order-line records were already identified by validation.
    # All copies are excluded here because they are quarantined for investigation.
    order_lines = order_lines.loc[~order_lines.duplicated(keep=False)].copy()

    records = transform_orders(orders, order_lines)
    return write_json(records, output_path)


if __name__ == "__main__":
    workbook = Path("(ecommerce)P1-AmazingMartEU2.xlsx")
    path = generate_json(workbook)
    print(f"Generated {path}")
