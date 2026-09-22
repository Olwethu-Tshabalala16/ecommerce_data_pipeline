import numpy as np
import pandas as pd

from transformation.data_transformation import (
    combine_order_data,
    serialize_orders,
    standardize_column_names,
    standardize_types,
    transform_orders,
)


def orders_df():
    return pd.DataFrame([
        {
            "Order ID": "O1",
            "Order Date": "2014-01-02",
            "Customer Name": "Alice",
            "City": "Berlin",
            "Country": "Germany",
            "Region": "Central",
            "Segment": "Consumer",
            "Ship Date": "2014-01-05",
            "Ship Mode": "Standard Class",
            "State": "Berlin",
        }
    ])


def lines_df():
    return pd.DataFrame([
        {
            "Order ID": "O1",
            "Product Name": "Pen",
            "Discount": 0.2,
            "Sales": 10.5,
            "Profit": 2.5,
            "Quantity": 2,
            "Category": "Office Supplies",
            "Sub-Category": "Art",
        }
    ])


def test_standardize_column_names():
    result = standardize_column_names(orders_df())
    assert "orderId" in result.columns
    assert "Order ID" not in result.columns


def test_standardize_types():
    combined = combine_order_data(orders_df(), lines_df())
    assert combined["orderDate"].iloc[0] == "2014-01-02"
    assert isinstance(combined["quantity"].iloc[0], (int, np.integer))
    assert isinstance(combined["sales"].iloc[0], (float, np.floating))


def test_combine_preserves_order_line_grain():
    result = combine_order_data(orders_df(), lines_df())
    assert len(result) == 1
    assert result.iloc[0]["productName"] == "Pen"


def test_transform_orders_creates_java_ready_structure():
    result = transform_orders(orders_df(), lines_df())

    assert len(result) == 1
    assert result[0]["orderId"] == "O1"
    assert result[0]["customer"]["name"] == "Alice"
    assert result[0]["location"]["country"] == "Germany"
    assert result[0]["shipping"]["shipMode"] == "Standard Class"
    assert result[0]["orderLine"]["quantity"] == 2
    assert result[0]["orderLine"]["sales"] == 10.5


def test_multiple_order_lines_remain_multiple_records():
    lines = pd.concat([lines_df(), lines_df().assign(**{"Product Name": "Notebook"})])
    result = transform_orders(orders_df(), lines)
    assert len(result) == 2
    assert {record["orderLine"]["productName"] for record in result} == {"Pen", "Notebook"}


def test_serialize_orders_preserves_records():
    records = transform_orders(orders_df(), lines_df())
    assert serialize_orders(records) == records
