from pathlib import Path

import pandas as pd
import pytest

from validation.data_validation import (
    DataQualityError,
    check_quality_for_orchestration,
    generate_validation_report,
    quarantine_table_records,
    run_validation_pipeline,
    validate_data_types,
    validate_discount,
    validate_order_references,
    validate_positive_quantity,
    validate_positive_target,
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


def test_validate_data_types():
    data = pd.DataFrame({
        "orderDate": ["2024-01-01", "not-a-date", None],
        "quantity": [1, 2.5, "not-num"],
        "sales": [10.5, "abc", 20],
    })
    types = {
        "orderDate": "datetime",
        "quantity": "integer",
        "sales": "numeric",
    }
    invalid = validate_data_types(data, types)
    assert 1 in invalid.index
    assert 2 in invalid.index
    assert 0 not in invalid.index


def test_validate_positive_target():
    data = pd.DataFrame({"Target": [100, 0, -50, "invalid"]})
    invalid = validate_positive_target(data)
    assert len(invalid) == 3


def test_quarantine_table_records():
    data = pd.DataFrame({
        "Order ID": ["A1", "A2", "A3"],
        "Quantity": [1, -5, 2],
    }, index=[0, 1, 2])

    rule_failures = {
        "invalid_quantity": data.loc[[1]],
    }

    valid, quarantined = quarantine_table_records(data, rule_failures)
    assert len(valid) == 2
    assert list(valid["Order ID"]) == ["A1", "A3"]
    assert len(quarantined) == 1
    assert quarantined.iloc[0]["Order ID"] == "A2"
    assert quarantined.iloc[0]["quarantine_reason"] == "invalid_quantity"


def test_generate_validation_report_metrics(tmp_path: Path):
    report_file = tmp_path / "test_report.json"
    table_stats = {
        "Orders": {"total_rows": 10, "valid_rows": 9, "quarantined_rows": 1, "pass_rate_percent": 90.0, "rule_failures": {"missing_val": 1}},
    }
    rule_results = {
        "missing_val": pd.DataFrame({"id": [1]}),
        "clean_rule": pd.DataFrame(),
    }
    report = generate_validation_report(
        source_file="test.xlsx",
        table_stats=table_stats,
        rule_results=rule_results,
        quarantine_files={"Orders": "quarantine.csv"},
        output_path=report_file,
    )
    assert report["validation_status"] == "FAIL"
    assert report["summary"]["total_records_evaluated"] == 10
    assert report["summary"]["total_valid_records"] == 9
    assert report["summary"]["total_quarantined_records"] == 1
    assert report["summary"]["overall_pass_rate_percent"] == 90.0
    assert report["summary"]["rules_passed"] == 1
    assert report["summary"]["rules_failed"] == 1
    assert report_file.exists()


def test_check_quality_for_orchestration():
    report = {
        "summary": {
            "failed_rules": ["breakdown_exact_duplicates", "corrupted_keys"],
            "overall_pass_rate_percent": 95.0,
            "total_quarantined_records": 5,
        }
    }
    # Raises when corrupted_keys is unexpected
    with pytest.raises(DataQualityError, match="unexpected rule failure"):
        check_quality_for_orchestration(report, allowed_failed_rules={"breakdown_exact_duplicates"})

    # Passes when all failed rules are allowed
    check_quality_for_orchestration(report, allowed_failed_rules={"breakdown_exact_duplicates", "corrupted_keys"})


def test_run_validation_pipeline_e2e(tmp_path: Path):
    workbook_path = tmp_path / "test_workbook.xlsx"
    orders = pd.DataFrame({
        "Order ID": ["A1", "A2"],
        "Order Date": ["2024-01-01", "2024-01-02"],
        "Customer Name": ["Alice", "Bob"],
        "City": ["Berlin", "Munich"],
        "Country": ["Germany", "Germany"],
        "Region": ["Central", "Central"],
        "Segment": ["Consumer", "Corporate"],
        "Ship Date": ["2024-01-03", "2024-01-04"],
        "Ship Mode": ["Economy", "Express"],
        "State": ["Berlin", "Bavaria"],
    })
    breakdown = pd.DataFrame({
        "Order ID": ["A1", "A1", "A2"],
        "Product Name": ["Item 1", "Item 1", "Item 2"],
        "Category": ["Technology", "Technology", "Furniture"],
        "Sub-Category": ["Phones", "Phones", "Chairs"],
        "Quantity": [1, 1, 3],
        "Discount": [0.1, 0.1, 0.0],
        "Sales": [100, 100, 200],
        "Profit": [20, 20, 40],
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

    q_dir = tmp_path / "quarantine"
    r_dir = tmp_path / "reports"

    res = run_validation_pipeline(
        workbook_path=workbook_path,
        quarantine_dir=q_dir,
        reports_dir=r_dir,
        fail_on_error=False,
    )

    assert res.validation_status == "FAIL"  # due to exact duplicate pair
    assert len(res.clean_tables["ListOfOrders"]) == 2
    assert len(res.clean_tables["OrderBreakdown"]) == 1  # 2 duplicates removed
    assert len(res.quarantined_tables["OrderBreakdown"]) == 2
    assert (q_dir / "breakdown_exact_duplicates.csv").exists()
    assert (r_dir / "validation_report.json").exists()
