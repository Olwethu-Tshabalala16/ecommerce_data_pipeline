package com.olwethu.ecommerce.repository;

import com.olwethu.ecommerce.api.dto.CustomerResponse;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class CustomerRepository {
    private final JdbcTemplate jdbc;
    public CustomerRepository(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    public List<CustomerResponse> findCustomers(int limit, String segment) {
        String sql = """
            SELECT customer_key, customer_name, segment
            FROM warehouse.dim_customer
            WHERE (? = '' OR segment = ?)
            ORDER BY customer_name, customer_key
            LIMIT ?
            """;
        return jdbc.query(sql, (rs, row) -> new CustomerResponse(
                rs.getString("customer_key"), rs.getString("customer_name"),
                rs.getString("segment")),
                segment, segment, limit);
    }
}
