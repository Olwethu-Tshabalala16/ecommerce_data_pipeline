package com.olwethu.ecommerce.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class MetadataService {
    private final JdbcTemplate jdbc;

    public MetadataService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Map<String, Object> metadata() {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("warehouse", "ecommerce_dw");
        result.put("schema", "warehouse");
        result.put("tables", Map.of(
                "dim_customer", count("warehouse.dim_customer"),
                "dim_product", count("warehouse.dim_product"),
                "dim_location", count("warehouse.dim_location"),
                "dim_date", count("warehouse.dim_date"),
                "dim_ship_mode", count("warehouse.dim_ship_mode"),
                "dim_sales_target", count("warehouse.dim_sales_target"),
                "fact_order_sales", count("warehouse.fact_order_sales")
        ));
        return result;
    }

    private long count(String table) {
        return jdbc.queryForObject("SELECT COUNT(*) FROM " + table, Long.class);
    }
}
