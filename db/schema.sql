-- PostgreSQL source-layer schema for the AmazingMart e-commerce dataset.
-- This schema represents the source structures; it is not the analytical warehouse.

CREATE SCHEMA IF NOT EXISTS source;

CREATE TABLE IF NOT EXISTS source.orders (
    order_id VARCHAR(32) PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    region TEXT NOT NULL,
    segment TEXT NOT NULL,
    ship_date DATE NOT NULL,
    ship_mode TEXT NOT NULL,
    state TEXT NOT NULL,
    CONSTRAINT orders_ship_date_check CHECK (ship_date >= order_date)
);

CREATE TABLE IF NOT EXISTS source.order_lines (
    source_order_line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    product_name TEXT NOT NULL,
    discount NUMERIC(5,4) NOT NULL,
    sales NUMERIC(14,2) NOT NULL,
    profit NUMERIC(14,2) NOT NULL,
    quantity INTEGER NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    CONSTRAINT order_lines_order_fk
        FOREIGN KEY (order_id)
        REFERENCES source.orders(order_id),
    CONSTRAINT order_lines_discount_check
        CHECK (discount >= 0 AND discount <= 1),
    CONSTRAINT order_lines_sales_check
        CHECK (sales >= 0),
    CONSTRAINT order_lines_quantity_check
        CHECK (quantity > 0)
);

CREATE TABLE IF NOT EXISTS source.sales_targets (
    month_of_order_date DATE NOT NULL,
    category TEXT NOT NULL,
    target NUMERIC(14,2) NOT NULL,
    CONSTRAINT sales_targets_pk
        PRIMARY KEY (month_of_order_date, category),
    CONSTRAINT sales_targets_target_check
        CHECK (target >= 0)
);

-- Source-schema design notes:
-- * order_id is the business key for source.orders.
-- * order_lines uses a generated technical identifier because the source has
--   no reliable natural line identifier and contains exact duplicate rows.
-- * Negative profit is intentionally allowed because it can be valid business data.
-- * Sales targets are uniquely identified by month/category.
-- * The schema has been checked against the profiling and validation results.
-- * Runtime execution against a PostgreSQL server remains an environment-level
--   verification step and is not claimed by this repository change.
