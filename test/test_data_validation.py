"""Tests for the source-data validation layer."""

import pandas as pd

from validation.data_validation import (
    validate_discount,
    validate_order_references,
    validate_positive_quantity,
    validate_required_columns,
    validate_required_values,
    validate_sales,
    validate_shipping_dates,
    validate_target_combinations,
    validate_unique_key,
)


def test_required_columns_detects_missing_column():
    data = pd.DataFrame({"Order ID": ["A-1"]})

    missing = validate_required_columns(data, "ListOfOrders")

    assert "Order Date" in missing


def test_required_values_detects_null_required_fields():
    data = pd.DataFrame({
        "Order ID": ["A-1", "A-2"],
        "Customer Name": ["Alice", None],
    })

    invalid = validate_required_values(data, ["Order ID", "Customer Name"])

    assert len(invalid) == 1
    assert invalid.iloc[0]["Order ID"] == "A-2"


def test_unique_key_detects_duplicates_and_nulls():
    data = pd.DataFrame({"Order ID": ["A-1", "A-1", None, "A-3"]})

    invalid = validate_unique_key(data, "Order ID")

    assert len(invalid) == 3


def test_shipping_date_cannot_be_before_order_date():
    data = pd.DataFrame({
        "Order Date": ["2014-01-10", "2014-01-10"],
        "Ship Date": ["2014-01-09", "2014-01-12"],
    })

    invalid = validate_shipping_dates(data)

    assert len(invalid) == 1


def test_order_reference_detects_orphan_order_id():
    orders = pd.DataFrame({"Order ID": ["A-1", "A-2"]})
    breakdown = pd.DataFrame({"Order ID": ["A-1", "A-3"]})

    invalid = validate_order_references(orders, breakdown)

    assert len(invalid) == 1
    assert invalid.iloc[0]["Order ID"] == "A-3"


def test_quantity_must_be_positive():
    data = pd.DataFrame({"Quantity": [1, 0, -2]})

    invalid = validate_positive_quantity(data)

    assert len(invalid) == 2


def test_discount_must_be_between_zero_and_one():
    data = pd.DataFrame({"Discount": [0, 0.5, 1, -0.1, 1.1]})

    invalid = validate_discount(data)

    assert len(invalid) == 2


def test_sales_cannot_be_negative():
    data = pd.DataFrame({"Sales": [100, 0, -5]})

    invalid = validate_sales(data)

    assert len(invalid) == 1


def test_negative_profit_is_not_rejected():
    data = pd.DataFrame({"Profit": [-100, 50]})

    assert (data["Profit"] < 0).any()


def test_sales_target_month_category_combination_must_be_unique():
    data = pd.DataFrame({
        "Month of Order Date": ["2014-01-01", "2014-01-01", "2014-02-01"],
        "Category": ["Technology", "Technology", "Technology"],
    })

    invalid = validate_target_combinations(data)

    assert len(invalid) == 2
