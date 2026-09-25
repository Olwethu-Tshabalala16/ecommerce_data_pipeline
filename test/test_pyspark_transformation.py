import pytest
from pyspark.sql import SparkSession

from transformation.pyspark_transformation import (
    build_dim_customer,
    build_dim_date,
    build_dim_location,
    build_dim_product,
    build_dim_sales_target,
    build_dim_ship_mode,
    build_fact_order_sales,
    prepare_order_lines,
    prepare_orders,
    prepare_sales_targets,
)


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder
        .appName("test-pyspark-transformation")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    yield session
    session.stop()


@pytest.fixture
def source_data(spark):
    orders = spark.createDataFrame(
        [
            (
                "O1",
                "2014-01-02",
                "Alice",
                "Berlin",
                "Germany",
                "Central",
                "Consumer",
                "2014-01-05",
                "Standard Class",
                "Berlin",
            ),
        ],
        [
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
        ],
    )

    orders = (
        orders
        .withColumn("Order Date", orders["Order Date"].cast("date"))
        .withColumn("Ship Date", orders["Ship Date"].cast("date"))
    )

    lines = spark.createDataFrame(
        [
            (
                "O1",
                "Pen",
                0.2,
                10.50,
                2.50,
                2,
                "Office Supplies",
                "Art",
            ),
            (
                "O1",
                "Notebook",
                0.1,
                20.00,
                5.00,
                1,
                "Office Supplies",
                "Paper",
            ),
        ],
        [
            "Order ID",
            "Product Name",
            "Discount",
            "Sales",
            "Profit",
            "Quantity",
            "Category",
            "Sub-Category",
        ],
    )

    targets = spark.createDataFrame(
        [
            (
                "2014-01-01",
                "Office Supplies",
                1000.00,
            ),
        ],
        [
            "Month of Order Date",
            "Category",
            "Target",
        ],
    )

    targets = targets.withColumn(
        "Month of Order Date",
        targets["Month of Order Date"].cast("date"),
    )

    return (
        prepare_orders(orders),
        prepare_order_lines(lines),
        prepare_sales_targets(targets),
    )


def test_prepare_orders_standardizes_columns(source_data):
    orders, _, _ = source_data

    assert "order_id" in orders.columns
    assert "order_date" in orders.columns
    assert "customer_name" in orders.columns
    assert "Order ID" not in orders.columns


def test_prepare_order_lines_preserves_order_line_grain(source_data):
    _, order_lines, _ = source_data

    assert order_lines.count() == 2
    assert order_lines.select("order_id").distinct().count() == 1


def test_customer_dimension_is_deterministic(source_data):
    orders, _, _ = source_data

    first = build_dim_customer(orders).collect()
    second = build_dim_customer(orders).collect()

    assert first == second
    assert len(first) == 1


def test_product_dimension_preserves_distinct_products(source_data):
    _, order_lines, _ = source_data

    products = build_dim_product(order_lines)

    assert products.count() == 2
    assert products.select("product_key").distinct().count() == 2


def test_location_dimension_uses_full_location_identity(source_data):
    orders, _, _ = source_data

    locations = build_dim_location(orders)

    assert locations.count() == 1
    assert locations.first()["city"] == "Berlin"
    assert locations.first()["country"] == "Germany"


def test_date_dimension_contains_order_and_ship_dates(source_data):
    orders, _, _ = source_data

    dates = build_dim_date(orders)

    assert dates.count() == 2

    date_values = {
        row["full_date"].strftime("%Y-%m-%d")
        for row in dates.collect()
    }

    assert "2014-01-02" in date_values
    assert "2014-01-05" in date_values


def test_ship_mode_dimension_is_distinct(source_data):
    orders, _, _ = source_data

    ship_modes = build_dim_ship_mode(orders)

    assert ship_modes.count() == 1
    assert ship_modes.first()["ship_mode"] == "Standard Class"


def test_sales_target_dimension_preserves_target(source_data):
    _, _, targets = source_data

    sales_targets = build_dim_sales_target(targets)

    assert sales_targets.count() == 1
    assert float(sales_targets.first()["target"]) == 1000.00


def test_fact_preserves_order_line_grain(source_data):
    orders, order_lines, targets = source_data

    dim_customer = build_dim_customer(orders)
    dim_product = build_dim_product(order_lines)
    dim_location = build_dim_location(orders)
    dim_ship_mode = build_dim_ship_mode(orders)
    dim_sales_target = build_dim_sales_target(targets)

    fact = build_fact_order_sales(
        orders=orders,
        order_lines=order_lines,
        dim_customer=dim_customer,
        dim_product=dim_product,
        dim_location=dim_location,
        dim_ship_mode=dim_ship_mode,
        dim_sales_target=dim_sales_target,
    )

    assert fact.count() == 2
    assert fact.select("order_id").distinct().count() == 1


def test_fact_contains_expected_measures(source_data):
    orders, order_lines, targets = source_data

    dim_customer = build_dim_customer(orders)
    dim_product = build_dim_product(order_lines)
    dim_location = build_dim_location(orders)
    dim_ship_mode = build_dim_ship_mode(orders)
    dim_sales_target = build_dim_sales_target(targets)

    fact = build_fact_order_sales(
        orders,
        order_lines,
        dim_customer,
        dim_product,
        dim_location,
        dim_ship_mode,
        dim_sales_target,
    )

    assert {
        "quantity",
        "sales",
        "profit",
        "discount",
    }.issubset(set(fact.columns))
