package com.olwethu.ecommerce.repository;

import com.olwethu.ecommerce.api.dto.ProductResponse;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class ProductRepository {
    private final JdbcTemplate jdbc;
    public ProductRepository(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    public List<ProductResponse> findProducts(int limit, String category) {
        String sql = """
            SELECT product_key, product_name, category, sub_category
            FROM warehouse.dim_product
            WHERE (? = '' OR category = ?)
            ORDER BY product_name, product_key
            LIMIT ?
            """;
        return jdbc.query(sql, (rs, row) -> new ProductResponse(
                rs.getString("product_key"), rs.getString("product_name"),
                rs.getString("category"), rs.getString("sub_category")),
                category, category, limit);
    }
}
