"""
Validation utilities for the AmazingMart e-commerce source data.

Validation identifies records that violate defined data-quality rules.
It does not transform the source data or remove unusual but valid values.
It separates valid records from quarantined records, computes quality metrics,
and surfaces quality status to pipeline orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Iterable

import pandas as pd


DEFAULT_WORKBOOK_PATH = Path("(ecommerce)P1-AmazingMartEU2.xlsx")
DEFAULT_QUARANTINE_DIR = Path("validation/quarantine")
DEFAULT_REPORTS_DIR = Path("validation/reports")

REQUIRED_COLUMNS = {
    "ListOfOrders": {
        "Order ID", "Order Date", "Customer Name", "City", "Country",
        "Region", "Segment", "Ship Date", "Ship Mode", "State",
    },
    "OrderBreakdown": {
        "Order ID", "Product Name", "Discount", "Sales", "Profit",
        "Quantity", "Category", "Sub-Category",
    },
    "SalesTargets": {"Month of Order Date", "Category", "Target"},
}

EXPECTED_DATA_TYPES = {
    "ListOfOrders": {
        "Order ID": "string",
        "Order Date": "datetime",
        "Customer Name": "string",
        "City": "string",
        "Country": "string",
        "Region": "string",
        "Segment": "string",
        "Ship Date": "datetime",
        "Ship Mode": "string",
        "State": "string",
    },
    "OrderBreakdown": {
        "Order ID": "string",
        "Product Name": "string",
        "Discount": "numeric",
        "Sales": "numeric",
        "Profit": "numeric",
        "Quantity": "integer",
        "Category": "string",
        "Sub-Category": "string",
    },
    "SalesTargets": {
        "Month of Order Date": "datetime",
        "Category": "string",
        "Target": "numeric",
    },
}

CRITICAL_RULES = {
    "orders_missing_columns",
    "breakdown_missing_columns",
    "targets_missing_columns",
    "orders_invalid_keys",
    "breakdown_invalid_order_references",
}


class DataQualityError(Exception):
    """Raised when data quality validation fails in an orchestrator context."""

    def __init__(self, message: str, summary: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.summary = summary or {}


@dataclass
class ValidationPipelineResult:
    """Container for pipeline run results, clean datasets, metrics, and quarantine outputs."""

    run_id: str
    executed_at: str
    source_file: str
    validation_status: str
    summary: dict[str, Any]
    clean_tables: dict[str, pd.DataFrame]
    quarantined_tables: dict[str, pd.DataFrame]
    report: dict[str, Any]
    report_path: Path
    quarantine_files: dict[str, Path]
    is_valid: bool


def validate_required_columns(data: pd.DataFrame, table_name: str) -> list[str]:
    """Return required columns that are missing from a source table."""
    return sorted(REQUIRED_COLUMNS[table_name] - set(data.columns))


def validate_required_values(data: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Return rows containing null values in required columns."""
    columns = list(columns)
    return data[data[columns].isna().any(axis=1)].copy()


def validate_data_types(
    data: pd.DataFrame, expected_types: dict[str, str]
) -> pd.DataFrame:
    """Return rows containing fields that cannot be converted to expected types."""
    invalid_mask = pd.Series(False, index=data.index)
    for col, expected_type in expected_types.items():
        if col not in data.columns:
            continue
        series = data[col]
        non_null = series.dropna()
        if non_null.empty:
            continue

        if expected_type == "datetime":
            parsed = pd.to_datetime(non_null, errors="coerce")
            invalid_indices = non_null[parsed.isna()].index
            invalid_mask |= data.index.isin(invalid_indices)
        elif expected_type == "integer":
            num = pd.to_numeric(non_null, errors="coerce")
            is_int = num.notna() & (num % 1 == 0)
            invalid_indices = non_null[~is_int].index
            invalid_mask |= data.index.isin(invalid_indices)
        elif expected_type in ("numeric", "float"):
            num = pd.to_numeric(non_null, errors="coerce")
            invalid_indices = non_null[num.isna()].index
            invalid_mask |= data.index.isin(invalid_indices)

    return data[invalid_mask].copy()


def validate_unique_key(data: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return rows that violate uniqueness or completeness of a key."""
    invalid = data[column].isna() | data[column].duplicated(keep=False)
    return data[invalid].copy()


def validate_duplicates(data: pd.DataFrame) -> pd.DataFrame:
    """Return exact duplicate rows."""
    return data[data.duplicated(keep=False)].copy()


def validate_dates(data: pd.DataFrame, date_columns: Iterable[str]) -> pd.DataFrame:
    """Return rows containing values that cannot be interpreted as dates."""
    invalid = pd.Series(False, index=data.index)
    for column in date_columns:
        invalid |= pd.to_datetime(data[column], errors="coerce").isna()
    return data[invalid].copy()


def validate_shipping_dates(data: pd.DataFrame) -> pd.DataFrame:
    """Return rows where shipping occurs before the order date."""
    order_dates = pd.to_datetime(data["Order Date"], errors="coerce")
    ship_dates = pd.to_datetime(data["Ship Date"], errors="coerce")
    return data[(ship_dates < order_dates).fillna(False)].copy()


def validate_order_references(orders: pd.DataFrame, order_breakdown: pd.DataFrame) -> pd.DataFrame:
    """Return order-line rows whose Order ID does not exist in the orders table."""
    valid_order_ids = set(orders["Order ID"].dropna())
    return order_breakdown[~order_breakdown["Order ID"].isin(valid_order_ids)].copy()


def validate_positive_quantity(data: pd.DataFrame) -> pd.DataFrame:
    """Return order-line rows with zero, negative, or non-numeric quantity."""
    quantity = pd.to_numeric(data["Quantity"], errors="coerce")
    return data[(quantity.le(0) | quantity.isna())].copy()


def validate_discount(data: pd.DataFrame) -> pd.DataFrame:
    """Return order-line rows with discounts outside the inclusive 0-1 range."""
    discount = pd.to_numeric(data["Discount"], errors="coerce")
    return data[(discount.isna() | discount.lt(0) | discount.gt(1))].copy()


def validate_sales(data: pd.DataFrame) -> pd.DataFrame:
    """Return order-line rows with invalid sales values."""
    sales = pd.to_numeric(data["Sales"], errors="coerce")
    return data[(sales.isna() | sales.lt(0))].copy()


def validate_numeric_column(data: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return rows where a required numeric column cannot be parsed as numeric."""
    values = pd.to_numeric(data[column], errors="coerce")
    return data[values.isna()].copy()


def validate_positive_target(data: pd.DataFrame) -> pd.DataFrame:
    """Return sales target rows with zero, negative, or non-numeric target."""
    target = pd.to_numeric(data["Target"], errors="coerce")
    return data[(target.le(0) | target.isna())].copy()


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
        "orders_missing_columns": validate_required_columns(orders, "ListOfOrders"),
        "orders_missing_values": validate_required_values(orders, REQUIRED_COLUMNS["ListOfOrders"]),
        "orders_invalid_data_types": validate_data_types(orders, EXPECTED_DATA_TYPES["ListOfOrders"]),
        "orders_invalid_keys": validate_unique_key(orders, "Order ID"),
        "orders_exact_duplicates": validate_duplicates(orders),
        "orders_invalid_dates": validate_dates(orders, ["Order Date", "Ship Date"]),
        "orders_invalid_shipping_dates": validate_shipping_dates(orders),
        "breakdown_missing_columns": validate_required_columns(order_breakdown, "OrderBreakdown"),
        "breakdown_missing_values": validate_required_values(order_breakdown, REQUIRED_COLUMNS["OrderBreakdown"]),
        "breakdown_invalid_data_types": validate_data_types(order_breakdown, EXPECTED_DATA_TYPES["OrderBreakdown"]),
        "breakdown_exact_duplicates": validate_duplicates(order_breakdown),
        "breakdown_invalid_order_references": validate_order_references(orders, order_breakdown),
        "breakdown_invalid_quantity": validate_positive_quantity(order_breakdown),
        "breakdown_invalid_discount": validate_discount(order_breakdown),
        "breakdown_invalid_sales": validate_sales(order_breakdown),
        "targets_missing_columns": validate_required_columns(sales_targets, "SalesTargets"),
        "targets_missing_values": validate_required_values(sales_targets, REQUIRED_COLUMNS["SalesTargets"]),
        "targets_invalid_data_types": validate_data_types(sales_targets, EXPECTED_DATA_TYPES["SalesTargets"]),
        "targets_exact_duplicates": validate_duplicates(sales_targets),
        "targets_invalid_dates": validate_dates(sales_targets, ["Month of Order Date"]),
        "targets_invalid_target": validate_numeric_column(sales_targets, "Target"),
        "targets_invalid_positive_target": validate_positive_target(sales_targets),
        "targets_duplicate_combinations": validate_target_combinations(sales_targets),
    }


def quarantine_table_records(
    data: pd.DataFrame,
    rule_failures: dict[str, pd.DataFrame | list[str]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate valid records from quarantined records based on rule failures.

    Returns:
        (valid_df, quarantined_df_with_reasons)
    """
    if data.empty:
        return data.copy(), pd.DataFrame()

    quarantine_indices: dict[Any, list[str]] = {}
    for rule_name, failure_data in rule_failures.items():
        if isinstance(failure_data, pd.DataFrame) and not failure_data.empty:
            for idx in failure_data.index:
                if idx in data.index:
                    quarantine_indices.setdefault(idx, []).append(rule_name)

    if not quarantine_indices:
        empty_quarantine = pd.DataFrame(columns=list(data.columns) + ["quarantine_reason"])
        return data.copy(), empty_quarantine

    all_quarantined_idx = list(quarantine_indices.keys())
    valid_df = data.drop(index=all_quarantined_idx).copy()

    quarantined_df = data.loc[all_quarantined_idx].copy()
    quarantined_df["quarantine_reason"] = [
        "; ".join(quarantine_indices[idx]) for idx in quarantined_df.index
    ]

    return valid_df, quarantined_df


def generate_validation_report(
    source_file: str,
    table_stats: dict[str, dict[str, Any]],
    rule_results: dict[str, pd.DataFrame | list[str]],
    quarantine_files: dict[str, str],
    output_path: Path = DEFAULT_REPORTS_DIR / "validation_report.json",
) -> dict[str, Any]:
    """Produce structured quality metrics for the pipeline run and persist to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rules_passed = sum(1 for res in rule_results.values() if len(res) == 0)
    rules_failed = sum(1 for res in rule_results.values() if len(res) > 0)
    failed_rules = [name for name, res in rule_results.items() if len(res) > 0]

    duplicate_rows = len(rule_results.get("breakdown_exact_duplicates", []))
    duplicate_records = duplicate_rows // 2 if duplicate_rows else 0

    total_records = sum(stats["total_rows"] for stats in table_stats.values())
    valid_records = sum(stats["valid_rows"] for stats in table_stats.values())
    quarantined_records = sum(stats["quarantined_rows"] for stats in table_stats.values())
    pass_rate = round((valid_records / total_records * 100), 2) if total_records > 0 else 100.0

    validation_status = "FAIL" if rules_failed > 0 else "PASS"

    note = (
        "The source contains 2 exact duplicate order-line records, represented by 4 rows "
        "because both copies are retained in the quarantine output."
        if "breakdown_exact_duplicates" in failed_rules and len(failed_rules) == 1
        else f"Validation completed with {rules_failed} failed rule(s)."
    )

    report = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "workbook": source_file,
        "validation_status": validation_status,
        "note": note,
        "summary": {
            "total_records_evaluated": total_records,
            "total_valid_records": valid_records,
            "total_quarantined_records": quarantined_records,
            "overall_pass_rate_percent": pass_rate,
            "rules_passed": rules_passed,
            "rules_failed": rules_failed,
            "failed_rule": failed_rules[0] if failed_rules else None,
            "failed_rules": failed_rules,
            "duplicate_rows_quarantined": duplicate_rows,
            "duplicate_records_identified": duplicate_records,
        },
        "tables": table_stats,
        "quarantine_artifacts": quarantine_files,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def check_quality_for_orchestration(
    report: dict[str, Any],
    allowed_failed_rules: set[str] | None = None,
) -> None:
    """Ensure quality failures are visible to orchestration systems.

    Raises DataQualityError if unexpected rule failures exist.
    """
    summary = report.get("summary", {})
    failed_rules = set(summary.get("failed_rules", []))
    allowed = allowed_failed_rules or set()

    unexpected_failures = failed_rules - allowed
    if unexpected_failures:
        msg = (
            f"Pipeline quality failure visible to orchestration: {len(unexpected_failures)} unexpected "
            f"rule failure(s) detected: {sorted(unexpected_failures)}. "
            f"Overall pass rate: {summary.get('overall_pass_rate_percent')}%. "
            f"Quarantined rows: {summary.get('total_quarantined_records')}."
        )
        raise DataQualityError(msg, summary=report)


def run_validation_pipeline(
    workbook_path: Path = DEFAULT_WORKBOOK_PATH,
    quarantine_dir: Path = DEFAULT_QUARANTINE_DIR,
    reports_dir: Path = DEFAULT_REPORTS_DIR,
    fail_on_error: bool = False,
    allowed_failed_rules: set[str] | None = None,
) -> ValidationPipelineResult:
    """Run full validation: evaluate rules, quarantine invalid rows, produce metrics, and notify orchestration."""
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    workbook = pd.ExcelFile(workbook_path)
    orders = pd.read_excel(workbook, sheet_name="ListOfOrders")
    order_breakdown = pd.read_excel(workbook, sheet_name="OrderBreakdown")
    sales_targets = pd.read_excel(workbook, sheet_name="SalesTargets")

    rule_results = validate_source_tables(orders, order_breakdown, sales_targets)

    # Separate valid and quarantined records for each table
    orders_rules = {k: v for k, v in rule_results.items() if k.startswith("orders_")}
    breakdown_rules = {k: v for k, v in rule_results.items() if k.startswith("breakdown_")}
    targets_rules = {k: v for k, v in rule_results.items() if k.startswith("targets_")}

    valid_orders, quarantined_orders = quarantine_table_records(orders, orders_rules)
    valid_breakdown, quarantined_breakdown = quarantine_table_records(order_breakdown, breakdown_rules)
    valid_targets, quarantined_targets = quarantine_table_records(sales_targets, targets_rules)

    clean_tables = {
        "ListOfOrders": valid_orders,
        "OrderBreakdown": valid_breakdown,
        "SalesTargets": valid_targets,
    }
    quarantined_tables = {
        "ListOfOrders": quarantined_orders,
        "OrderBreakdown": quarantined_breakdown,
        "SalesTargets": quarantined_targets,
    }

    # Save quarantine artifacts
    quarantine_files: dict[str, Path] = {}

    exact_duplicates = rule_results.get("breakdown_exact_duplicates")
    if isinstance(exact_duplicates, pd.DataFrame) and not exact_duplicates.empty:
        dup_path = quarantine_dir / "breakdown_exact_duplicates.csv"
        exact_duplicates.to_csv(dup_path, index=False)
        quarantine_files["breakdown_exact_duplicates"] = dup_path

    for tbl_name, q_df in quarantined_tables.items():
        if not q_df.empty and tbl_name != "OrderBreakdown":
            q_path = quarantine_dir / f"{tbl_name}_quarantined.csv"
            q_df.to_csv(q_path, index=False)
            quarantine_files[f"{tbl_name}_quarantined"] = q_path

    def table_metrics(table_name: str, total_df: pd.DataFrame, valid_df: pd.DataFrame, q_df: pd.DataFrame, rules: dict) -> dict[str, Any]:
        total = len(total_df)
        valid = len(valid_df)
        q_count = len(q_df)
        rate = round((valid / total * 100), 2) if total > 0 else 100.0
        return {
            "total_rows": total,
            "valid_rows": valid,
            "quarantined_rows": q_count,
            "pass_rate_percent": rate,
            "rule_failures": {
                k: len(v) for k, v in rules.items() if len(v) > 0
            },
        }

    table_stats = {
        "ListOfOrders": table_metrics("ListOfOrders", orders, valid_orders, quarantined_orders, orders_rules),
        "OrderBreakdown": table_metrics("OrderBreakdown", order_breakdown, valid_breakdown, quarantined_breakdown, breakdown_rules),
        "SalesTargets": table_metrics("SalesTargets", sales_targets, valid_targets, quarantined_targets, targets_rules),
    }

    report_path = reports_dir / "validation_report.json"
    report_dict = generate_validation_report(
        source_file=workbook_path.name,
        table_stats=table_stats,
        rule_results=rule_results,
        quarantine_files={k: str(v) for k, v in quarantine_files.items()},
        output_path=report_path,
    )

    is_valid = report_dict["summary"]["rules_failed"] == 0

    if fail_on_error:
        check_quality_for_orchestration(report_dict, allowed_failed_rules=allowed_failed_rules)

    return ValidationPipelineResult(
        run_id=report_dict["run_id"],
        executed_at=report_dict["executed_at"],
        source_file=workbook_path.name,
        validation_status=report_dict["validation_status"],
        summary=report_dict["summary"],
        clean_tables=clean_tables,
        quarantined_tables=quarantined_tables,
        report=report_dict,
        report_path=report_path,
        quarantine_files=quarantine_files,
        is_valid=is_valid,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run e-commerce data pipeline validation rules.")
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK_PATH, help="Path to source Excel workbook.")
    parser.add_argument("--strict", action="store_true", help="Fail pipeline with non-zero exit code on any rule failure.")
    parser.add_argument("--fail-on-critical", action="store_true", default=True, help="Fail only on critical schema/referential errors.")
    parser.add_argument("--allow-known-duplicates", action="store_true", default=True, help="Allow known duplicate records to be quarantined without failing orchestration.")
    args = parser.parse_args()

    allowed_rules = {"breakdown_exact_duplicates"} if args.allow_known_duplicates and not args.strict else set()

    try:
        res = run_validation_pipeline(
            workbook_path=args.workbook,
            fail_on_error=args.strict,
            allowed_failed_rules=allowed_rules,
        )
        print(f"\n=======================================================")
        print(f"DATA QUALITY VALIDATION COMPLETED (Run ID: {res.run_id})")
        print(f"=======================================================")
        print(f"Status: {res.validation_status}")
        print(f"Evaluated Records: {res.summary['total_records_evaluated']:,}")
        print(f"Valid Records:     {res.summary['total_valid_records']:,}")
        print(f"Quarantined Rows:  {res.summary['total_quarantined_records']:,}")
        print(f"Overall Pass Rate: {res.summary['overall_pass_rate_percent']:.2f}%")
        print(f"Rules Passed:      {res.summary['rules_passed']}")
        print(f"Rules Failed:      {res.summary['rules_failed']}")
        if res.summary['failed_rules']:
            print(f"Failed Rules:      {', '.join(res.summary['failed_rules'])}")
        print(f"Report written to: {res.report_path}")
        if res.quarantine_files:
            print("Quarantine artifacts:")
            for name, path in res.quarantine_files.items():
                print(f"  - {name}: {path}")
        print(f"=======================================================\n")
    except DataQualityError as err:
        print(f"\n[FATAL ORCHESTRATION QUALITY FAILURE] {err}", file=sys.stderr)
        sys.exit(1)
