"""Load curated Parquet datasets into the PostgreSQL analytical warehouse.

The loader performs a transactional full refresh. This is intentionally simple and
idempotent for the current batch-oriented source: a successful run replaces the
warehouse contents with the current curated snapshot, while a failure rolls back
the load.
"""

import os
from pathlib import Path

import psycopg
from pyspark.sql import SparkSession


ROOT = Path(__file__).resolve().parents[1]
CURATED_DIR = ROOT / "curated"
SCHEMA_FILE = ROOT / "db" / "warehouse_schema.sql"
DATABASE = os.getenv("WAREHOUSE_DB", "ecommerce_dw")
USER = os.getenv("WAREHOUSE_USER", "postgres")
HOST = os.getenv("WAREHOUSE_HOST")
PORT = os.getenv("WAREHOUSE_PORT", "5432")
PASSWORD = os.getenv("WAREHOUSE_PASSWORD")

TABLES = (
    "dim_customer",
    "dim_product",
    "dim_location",
    "dim_date",
    "dim_ship_mode",
    "dim_sales_target",
    "fact_order_sales",
)

COLUMNS = {
    "dim_customer": ("customer_key", "customer_name", "segment"),
    "dim_product": ("product_key", "product_name", "category", "sub_category"),
    "dim_location": ("location_key", "city", "state", "country", "region"),
    "dim_date": (
        "date_key", "full_date", "year", "quarter", "month", "month_name",
        "day_of_month", "day_of_week", "week_of_year",
    ),
    "dim_ship_mode": ("ship_mode_key", "ship_mode"),
    "dim_sales_target": (
        "sales_target_key", "month_date", "year", "month", "category", "target",
    ),
    "fact_order_sales": (
        "order_id", "order_date_key", "ship_date_key", "customer_key",
        "product_key", "location_key", "ship_mode_key", "sales_target_key",
        "quantity", "sales", "profit", "discount",
    ),
}


def create_spark_session():
    return (
        SparkSession.builder
        .master("local[*]")
        .appName("ecommerce-warehouse-load")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def connect():
    kwargs = {
        "dbname": DATABASE,
        "user": USER,
        "port": PORT,
    }
    if HOST:
        kwargs["host"] = HOST
    if PASSWORD:
        kwargs["password"] = PASSWORD
    return psycopg.connect(**kwargs)


def read_curated(spark, table):
    path = CURATED_DIR / table
    if not path.exists():
        raise FileNotFoundError(f"Curated dataset not found: {path}")
    return spark.read.parquet(str(path))


def insert_dataframe(cur, table, dataframe):
    columns = COLUMNS[table]
    column_sql = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = (
        f"INSERT INTO warehouse.{table} ({column_sql}) "
        f"VALUES ({placeholders})"
    )

    rows = (
        tuple(row[column] for column in columns)
        for row in dataframe.toLocalIterator()
    )
    cur.executemany(sql, rows)


def load():
    spark = create_spark_session()
    try:
        dataframes = {table: read_curated(spark, table) for table in TABLES}

        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_FILE.read_text(encoding="utf-8"))

                # Full refresh in dependency order. The transaction makes the
                # complete replacement atomic: a failed load leaves the prior
                # warehouse snapshot intact.
                cur.execute(
                    """
                    TRUNCATE TABLE
                        warehouse.fact_order_sales,
                        warehouse.dim_sales_target,
                        warehouse.dim_ship_mode,
                        warehouse.dim_location,
                        warehouse.dim_product,
                        warehouse.dim_customer,
                        warehouse.dim_date
                    RESTART IDENTITY CASCADE
                    """
                )

                for table in TABLES:
                    insert_dataframe(cur, table, dataframes[table])

                expected = {
                    table: dataframes[table].count() for table in TABLES
                }
                actual = {}
                for table in TABLES:
                    cur.execute(f"SELECT COUNT(*) FROM warehouse.{table}")
                    actual[table] = cur.fetchone()[0]

                if actual != expected:
                    raise RuntimeError(
                        f"Warehouse row-count mismatch: expected={expected}, "
                        f"actual={actual}"
                    )

        print("Warehouse load completed successfully.")
        for table in TABLES:
            print(f"{table}: {expected[table]}")
    finally:
        spark.stop()


if __name__ == "__main__":
    load()
