# Spring Boot Data API

The API exposes selected data from the PostgreSQL `warehouse` schema.

## Run

From the repository root:

```bash
mvn spring-boot:run
```

The application defaults to:

- PostgreSQL database: `ecommerce_dw`
- PostgreSQL host: `localhost`
- PostgreSQL port: `5432`
- HTTP port: `8080`

These can be overridden with environment variables:

- `WAREHOUSE_JDBC_URL`
- `WAREHOUSE_USER`
- `WAREHOUSE_PASSWORD`
- `SERVER_PORT`

## Endpoints

### Health

`GET /api/v1/health`

Returns application availability without querying the warehouse.

### Products

`GET /api/v1/products?limit=50&category=Furniture`

Returns product dimension records. `category` is optional and `limit` is constrained to 1–200.

### Customers

`GET /api/v1/customers?limit=50&segment=Consumer`

Returns customer dimension records. `segment` is optional and `limit` is constrained to 1–200.

### Order lines

`GET /api/v1/orders/lines?limit=50&orderId=...`

Returns the warehouse fact rows at the existing order-line grain. `orderId` is optional and `limit` is constrained to 1–200.

### Warehouse metadata

`GET /api/v1/metadata`

Returns the warehouse name, schema, and current row counts for the seven warehouse tables.

## Layering

The application follows:

```text
Controller
    ↓
Service
    ↓
Repository
    ↓
PostgreSQL warehouse
```

Controllers define the HTTP contract, services provide the application boundary, and repositories contain SQL access.

The API deliberately exposes only entities represented by the warehouse. Payment and inventory endpoints are not created because those entities are absent from the source dataset.
