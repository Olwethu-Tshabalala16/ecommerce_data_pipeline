# PostgreSQL Source Schema

## Purpose

The `source` schema represents the three datasets supplied by the current AmazingMart workbook. It is intentionally separate from the future analytical warehouse.

The schema is based on the results of source profiling and validation. It does not introduce unsupported entities such as payments or inventory.

## Tables

### `source.orders`

Represents the `ListOfOrders` sheet.

**Grain:** one row per order.

**Primary key:** `order_id`, because profiling confirmed that Order ID is complete and unique in the source order table.

The table stores order dates, customer attributes, geographic attributes, and shipping attributes.

`ship_date >= order_date` is enforced because the source validation rules define shipment before order as invalid.

### `source.order_lines`

Represents the `OrderBreakdown` sheet.

**Grain:** one row per product line within an order.

`order_id` is a foreign key to `source.orders(order_id)`, representing the order-to-order-line relationship.

The source does not provide a reliable natural line identifier. Therefore, `source_order_line_id` is a database-generated technical identifier. It is not treated as a business key and does not alter the source grain.

Exact duplicate order-line records were found during validation. The table therefore does not impose uniqueness on the combination of order and product attributes. The duplicate records are handled by the validation/quarantine process rather than being silently rejected by the source schema.

### `source.sales_targets`

Represents the `SalesTargets` sheet.

**Grain:** one row per month/category combination.

The composite primary key `(month_of_order_date, category)` reflects the profiled uniqueness of the month/category combination.

## Data Type Decisions

| Source field type | PostgreSQL type | Reason |
|---|---|---|
| Order ID | `VARCHAR(32)` | Identifier is textual and should not be treated as numeric |
| Dates | `DATE` | Source values represent calendar dates |
| Names / geographic / categorical fields | `TEXT` | Variable-length descriptive values |
| Quantity | `INTEGER` | Discrete count of products |
| Discount | `NUMERIC(5,4)` | Decimal value requiring exact storage, with a 0–1 range |
| Sales / Profit / Target | `NUMERIC(14,2)` | Financial values should use exact decimal arithmetic rather than floating-point storage |
| Technical order-line identifier | `BIGINT GENERATED ALWAYS AS IDENTITY` | Database-generated technical identifier |

## Constraints

The schema enforces structural and known domain requirements that were established during profiling and validation:

- Orders require a non-null unique `order_id`.
- Order lines require a valid parent order.
- Shipment cannot occur before the order.
- Quantity must be greater than zero.
- Discount must be between 0 and 1 inclusive.
- Sales must be non-negative.
- Sales targets must be non-negative.
- Month/category combinations in sales targets must be unique.

Profit is intentionally allowed to be negative. A negative profit value represents a possible business outcome and is not automatically a data-quality failure.

## Source-to-Database Mapping

```text
ListOfOrders       -> source.orders
OrderBreakdown     -> source.order_lines
SalesTargets       -> source.sales_targets
```

The source schema is an implementation of the current source contract. It is not the final dimensional warehouse. Warehouse-specific surrogate keys and analytical dimensions will be introduced in the later warehouse implementation issue.

## Loading Consideration

The current workbook is a static batch source and does not provide an `updated_at` column or another reliable change-tracking field. Therefore, this schema does not claim to support CDC or watermark-based incremental loading. An appropriate batch/reload strategy can be introduced later if the source contract changes or sufficient metadata becomes available.
