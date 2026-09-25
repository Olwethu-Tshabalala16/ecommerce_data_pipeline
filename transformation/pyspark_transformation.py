"""PySpark transformation layer for the AmazingMart e-commerce dataset.

Consumes validated source tables and produces curated, warehouse-ready
dimensional datasets and an order-line fact dataset.

Fact grain:
    One row = one product line within an order.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from validation.data_validation import run_validation_pipeline


DEFAULT_WORKBOOK = Path("(ecommerce)P1-AmazingMartEU2.xlsx")
DEFAULT_OUTPUT_DIR = Path("curated")


def create_spark_session() -> SparkSession:
    """Create the local Spark session used by the transformation layer."""
    return (
        SparkSession.builder
        .appName("AmazingMart-PySpark-Transformation")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def _normalise_value(value: Any, field_type: Any) -> Any:
    """Convert Pandas scalar values into values accepted by Spark schemas."""
    if value is None:
        return None

    if field_type == DateType():
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return value

    if isinstance(field_type, DecimalType):
        return Decimal(str(value))

    if isinstance(value, float) and value != value:
        return None

    return value


def pandas_to_spark(
    spark: SparkSession,
    dataframe,
    schema: StructType,
) -> DataFrame:
    """Convert a validated Pandas DataFrame into a typed Spark DataFrame."""
    records = []

    for row in dataframe.to_dict(orient="records"):
        records.append(
            tuple(
                _normalise_value(
                    row[field.name],
                    field.dataType,
                )
                for field in schema.fields
            )
        )

    return spark.createDataFrame(records, schema=schema)


def source_schemas() -> dict[str, StructType]:
    """Return explicit schemas for the validated source tables."""
    return {
        "ListOfOrders": StructType([
            StructField("Order ID", StringType(), False),
            StructField("Order Date", DateType(), False),
            StructField("Customer Name", StringType(), False),
            StructField("City", StringType(), False),
            StructField("Country", StringType(), False),
            StructField("Region", StringType(), False),
            StructField("Segment", StringType(), False),
            StructField("Ship Date", DateType(), False),
            StructField("Ship Mode", StringType(), False),
            StructField("State", StringType(), False),
        ]),
        "OrderBreakdown": StructType([
            StructField("Order ID", StringType(), False),
            StructField("Product Name", StringType(), False),
            StructField("Discount", DecimalType(10, 4), False),
            StructField("Sales", DecimalType(14, 2), False),
            StructField("Profit", DecimalType(14, 2), False),
            StructField("Quantity", IntegerType(), False),
            StructField("Category", StringType(), False),
            StructField("Sub-Category", StringType(), False),
        ]),
        "SalesTargets": StructType([
            StructField("Month of Order Date", DateType(), False),
            StructField("Category", StringType(), False),
            StructField("Target", DecimalType(14, 2), False),
        ]),
    }


def prepare_orders(orders: DataFrame) -> DataFrame:
    """Standardise validated order-level fields."""
    return orders.select(
        F.col("Order ID").alias("order_id"),
        F.col("Order Date").alias("order_date"),
        F.trim(F.col("Customer Name")).alias("customer_name"),
        F.trim(F.col("City")).alias("city"),
        F.trim(F.col("Country")).alias("country"),
        F.trim(F.col("Region")).alias("region"),
        F.trim(F.col("Segment")).alias("segment"),
        F.col("Ship Date").alias("ship_date"),
        F.trim(F.col("Ship Mode")).alias("ship_mode"),
        F.trim(F.col("State")).alias("state"),
    )


def prepare_order_lines(order_lines: DataFrame) -> DataFrame:
    """Standardise validated order-line fields."""
    return order_lines.select(
        F.col("Order ID").alias("order_id"),
        F.trim(F.col("Product Name")).alias("product_name"),
        F.col("Discount").cast(DecimalType(10, 4)).alias("discount"),
        F.col("Sales").cast(DecimalType(14, 2)).alias("sales"),
        F.col("Profit").cast(DecimalType(14, 2)).alias("profit"),
        F.col("Quantity").cast(IntegerType()).alias("quantity"),
        F.trim(F.col("Category")).alias("category"),
        F.trim(F.col("Sub-Category")).alias("sub_category"),
    )


def prepare_sales_targets(targets: DataFrame) -> DataFrame:
    """Standardise validated monthly sales targets."""
    return targets.select(
        F.col("Month of Order Date").alias("month_date"),
        F.trim(F.col("Category")).alias("category"),
        F.col("Target").cast(DecimalType(14, 2)).alias("target"),
    )


def build_dim_customer(orders: DataFrame) -> DataFrame:
    """Build the customer dimension."""
    customers = orders.select(
        "customer_name",
        "segment",
    ).dropDuplicates()

    return customers.select(
        F.sha2(
            F.concat_ws("||", F.col("customer_name"), F.col("segment")),
            256,
        ).alias("customer_key"),
        F.col("customer_name"),
        F.col("segment"),
    )


def build_dim_product(order_lines: DataFrame) -> DataFrame:
    """Build the product dimension."""
    products = order_lines.select(
        "product_name",
        "category",
        "sub_category",
    ).dropDuplicates()

    return products.select(
        F.sha2(
            F.concat_ws(
                "||",
                F.col("product_name"),
                F.col("category"),
                F.col("sub_category"),
            ),
            256,
        ).alias("product_key"),
        F.col("product_name"),
        F.col("category"),
        F.col("sub_category"),
    )


def build_dim_location(orders: DataFrame) -> DataFrame:
    """Build the location dimension."""
    locations = orders.select(
        "city",
        "state",
        "country",
        "region",
    ).dropDuplicates()

    return locations.select(
        F.sha2(
            F.concat_ws(
                "||",
                F.col("city"),
                F.col("state"),
                F.col("country"),
                F.col("region"),
            ),
            256,
        ).alias("location_key"),
        F.col("city"),
        F.col("state"),
        F.col("country"),
        F.col("region"),
    )


def build_dim_date(orders: DataFrame) -> DataFrame:
    """Build a date dimension from order and shipping dates."""
    dates = (
        orders.select(F.col("order_date").alias("date"))
        .union(orders.select(F.col("ship_date").alias("date")))
        .distinct()
    )

    return dates.select(
        F.date_format("date", "yyyyMMdd").cast(IntegerType()).alias("date_key"),
        F.col("date").alias("full_date"),
        F.year("date").alias("year"),
        F.quarter("date").alias("quarter"),
        F.month("date").alias("month"),
        F.date_format("date", "MMMM").alias("month_name"),
        F.dayofmonth("date").alias("day_of_month"),
        F.dayofweek("date").alias("day_of_week"),
        F.weekofyear("date").alias("week_of_year"),
    )


def build_dim_ship_mode(orders: DataFrame) -> DataFrame:
    """Build the shipping-mode dimension."""
    ship_modes = orders.select("ship_mode").dropDuplicates()

    return ship_modes.select(
        F.sha2(F.col("ship_mode"), 256).alias("ship_mode_key"),
        F.col("ship_mode"),
    )


def build_dim_sales_target(targets: DataFrame) -> DataFrame:
    """Build the sales-target dimension."""
    return targets.select(
        F.sha2(
            F.concat_ws(
                "||",
                F.date_format("month_date", "yyyy-MM-dd"),
                F.col("category"),
            ),
            256,
        ).alias("sales_target_key"),
        F.col("month_date"),
        F.year("month_date").alias("year"),
        F.month("month_date").alias("month"),
        F.col("category"),
        F.col("target"),
    )


def build_fact_order_sales(
    orders: DataFrame,
    order_lines: DataFrame,
    dim_customer: DataFrame,
    dim_product: DataFrame,
    dim_location: DataFrame,
    dim_ship_mode: DataFrame,
    dim_sales_target: DataFrame,
) -> DataFrame:
    """Build the central fact table at one product-line-per-order grain."""
    combined = order_lines.join(orders, on="order_id", how="inner")

    combined = combined.join(
        dim_customer,
        on=["customer_name", "segment"],
        how="left",
    )

    combined = combined.join(
        dim_product,
        on=["product_name", "category", "sub_category"],
        how="left",
    )

    combined = combined.join(
        dim_location,
        on=["city", "state", "country", "region"],
        how="left",
    )

    combined = combined.join(
        dim_ship_mode,
        on=["ship_mode"],
        how="left",
    )

    combined = combined.withColumn(
        "month_date",
        F.to_date(F.date_format(F.col("order_date"), "yyyy-MM-01")),
    )

    combined = combined.join(
        dim_sales_target,
        on=["month_date", "category"],
        how="left",
    )

    return combined.select(
        F.col("order_id"),
        F.date_format("order_date", "yyyyMMdd")
        .cast(IntegerType())
        .alias("order_date_key"),
        F.date_format("ship_date", "yyyyMMdd")
        .cast(IntegerType())
        .alias("ship_date_key"),
        F.col("customer_key"),
        F.col("product_key"),
        F.col("location_key"),
        F.col("ship_mode_key"),
        F.col("sales_target_key"),
        F.col("quantity").cast(IntegerType()).alias("quantity"),
        F.col("sales").cast(DecimalType(14, 2)).alias("sales"),
        F.col("profit").cast(DecimalType(14, 2)).alias("profit"),
        F.col("discount").cast(DecimalType(10, 4)).alias("discount"),
    )


def write_curated_dataset(
    dataframe: DataFrame,
    output_dir: Path,
    dataset_name: str,
) -> None:
    """Write one curated dataset as Parquet."""
    (
        dataframe.write
        .mode("overwrite")
        .parquet(str(output_dir / dataset_name))
    )


def transform_validated_data(
    spark: SparkSession,
    workbook_path: Path = DEFAULT_WORKBOOK,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, DataFrame]:
    """Validate the source and transform its clean tables into curated datasets."""
    validation_result = run_validation_pipeline(
        workbook_path=workbook_path,
        fail_on_error=True,
        allowed_failed_rules={"breakdown_exact_duplicates"},
    )

    clean_tables = validation_result.clean_tables
    schemas = source_schemas()

    orders = prepare_orders(
        pandas_to_spark(spark, clean_tables["ListOfOrders"], schemas["ListOfOrders"])
    )
    order_lines = prepare_order_lines(
        pandas_to_spark(
            spark,
            clean_tables["OrderBreakdown"],
            schemas["OrderBreakdown"],
        )
    )
    targets = prepare_sales_targets(
        pandas_to_spark(spark, clean_tables["SalesTargets"], schemas["SalesTargets"])
    )

    dim_customer = build_dim_customer(orders)
    dim_product = build_dim_product(order_lines)
    dim_location = build_dim_location(orders)
    dim_date = build_dim_date(orders)
    dim_ship_mode = build_dim_ship_mode(orders)
    dim_sales_target = build_dim_sales_target(targets)

    fact_order_sales = build_fact_order_sales(
        orders=orders,
        order_lines=order_lines,
        dim_customer=dim_customer,
        dim_product=dim_product,
        dim_location=dim_location,
        dim_ship_mode=dim_ship_mode,
        dim_sales_target=dim_sales_target,
    )

    curated = {
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_location": dim_location,
        "dim_date": dim_date,
        "dim_ship_mode": dim_ship_mode,
        "dim_sales_target": dim_sales_target,
        "fact_order_sales": fact_order_sales,
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    for name, dataframe in curated.items():
        write_curated_dataset(dataframe, output_dir, name)

    return curated


def main() -> None:
    """Run the complete PySpark transformation."""
    spark = create_spark_session()

    try:
        curated = transform_validated_data(
            spark=spark,
            workbook_path=DEFAULT_WORKBOOK,
            output_dir=DEFAULT_OUTPUT_DIR,
        )

        print("\nPySpark transformation completed.")
        print("\nCurated datasets:")

        for name, dataframe in curated.items():
            print(f"\n{name}")
            print(f"Rows: {dataframe.count():,}")
            dataframe.printSchema()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
