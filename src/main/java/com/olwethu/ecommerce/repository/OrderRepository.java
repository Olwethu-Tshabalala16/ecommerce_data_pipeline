package com.olwethu.ecommerce.repository;

import com.olwethu.ecommerce.api.dto.OrderLineResponse;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class OrderRepository {
    private final JdbcTemplate jdbc;
    public OrderRepository(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    public List<OrderLineResponse> findOrderLines(int limit, String orderId) {
        String sql = """
            SELECT fact_order_sales_id, order_id, order_date_key, ship_date_key,
                   customer_key, product_key, location_key, ship_mode_key,
                   sales_target_key, quantity, sales, profit, discount
            FROM warehouse.fact_order_sales
            WHERE (? = '' OR order_id = ?)
            ORDER BY fact_order_sales_id
            LIMIT ?
            """;
        return jdbc.query(sql, (rs, row) -> new OrderLineResponse(
                rs.getLong("fact_order_sales_id"), rs.getString("order_id"),
                rs.getInt("order_date_key"), rs.getInt("ship_date_key"),
                rs.getString("customer_key"), rs.getString("product_key"),
                rs.getString("location_key"), rs.getString("ship_mode_key"),
                rs.getString("sales_target_key"), rs.getInt("quantity"),
                rs.getBigDecimal("sales"), rs.getBigDecimal("profit"),
                rs.getBigDecimal("discount")),
                orderId, orderId, limit);
    }
}
