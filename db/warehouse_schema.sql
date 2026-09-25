-- Analytical warehouse schema for the AmazingMart e-commerce dataset.
-- Source-layer objects remain in the separate source schema.

CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_key VARCHAR(64) PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_key VARCHAR(64) PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_location (
    location_key VARCHAR(64) PRIMARY KEY,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    country TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_ship_mode (
    ship_mode_key VARCHAR(64) PRIMARY KEY,
    ship_mode TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS warehouse.dim_sales_target (
    sales_target_key VARCHAR(64) PRIMARY KEY,
    month_date DATE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    category TEXT NOT NULL,
    target NUMERIC(14,2) NOT NULL,
    CONSTRAINT dim_sales_target_month_category_unique
        UNIQUE (month_date, category)
);

CREATE TABLE IF NOT EXISTS warehouse.fact_order_sales (
    fact_order_sales_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    order_date_key INTEGER NOT NULL,
    ship_date_key INTEGER NOT NULL,
    customer_key VARCHAR(64) NOT NULL,
    product_key VARCHAR(64) NOT NULL,
    location_key VARCHAR(64) NOT NULL,
    ship_mode_key VARCHAR(64) NOT NULL,
    sales_target_key VARCHAR(64) NOT NULL,
    quantity INTEGER NOT NULL,
    sales NUMERIC(14,2) NOT NULL,
    profit NUMERIC(14,2) NOT NULL,
    discount NUMERIC(10,4) NOT NULL,

    CONSTRAINT fact_order_sales_order_date_fk
        FOREIGN KEY (order_date_key) REFERENCES warehouse.dim_date(date_key),
    CONSTRAINT fact_order_sales_ship_date_fk
        FOREIGN KEY (ship_date_key) REFERENCES warehouse.dim_date(date_key),
    CONSTRAINT fact_order_sales_customer_fk
        FOREIGN KEY (customer_key) REFERENCES warehouse.dim_customer(customer_key),
    CONSTRAINT fact_order_sales_product_fk
        FOREIGN KEY (product_key) REFERENCES warehouse.dim_product(product_key),
    CONSTRAINT fact_order_sales_location_fk
        FOREIGN KEY (location_key) REFERENCES warehouse.dim_location(location_key),
    CONSTRAINT fact_order_sales_ship_mode_fk
        FOREIGN KEY (ship_mode_key) REFERENCES warehouse.dim_ship_mode(ship_mode_key),
    CONSTRAINT fact_order_sales_sales_target_fk
        FOREIGN KEY (sales_target_key) REFERENCES warehouse.dim_sales_target(sales_target_key),

    CONSTRAINT fact_order_sales_quantity_check CHECK (quantity > 0),
    CONSTRAINT fact_order_sales_sales_check CHECK (sales >= 0),
    CONSTRAINT fact_order_sales_discount_check CHECK (discount >= 0 AND discount <= 1)
);

CREATE INDEX IF NOT EXISTS idx_fact_order_sales_order_date
    ON warehouse.fact_order_sales(order_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_sales_ship_date
    ON warehouse.fact_order_sales(ship_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_sales_customer
    ON warehouse.fact_order_sales(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_sales_product
    ON warehouse.fact_order_sales(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_sales_location
    ON warehouse.fact_order_sales(location_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_sales_ship_mode
    ON warehouse.fact_order_sales(ship_mode_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_sales_sales_target
    ON warehouse.fact_order_sales(sales_target_key);
