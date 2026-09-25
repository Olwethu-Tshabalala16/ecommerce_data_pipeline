package com.olwethu.ecommerce.service;

import com.olwethu.ecommerce.api.dto.ProductResponse;
import com.olwethu.ecommerce.repository.ProductRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ProductService {
    private final ProductRepository repository;
    public ProductService(ProductRepository repository) { this.repository = repository; }
    public List<ProductResponse> findProducts(int limit, String category) {
        return repository.findProducts(limit, category);
    }
}
