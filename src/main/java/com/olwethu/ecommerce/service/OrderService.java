package com.olwethu.ecommerce.service;

import com.olwethu.ecommerce.api.dto.OrderLineResponse;
import com.olwethu.ecommerce.repository.OrderRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class OrderService {
    private final OrderRepository repository;
    public OrderService(OrderRepository repository) { this.repository = repository; }
    public List<OrderLineResponse> findOrderLines(int limit, String orderId) {
        return repository.findOrderLines(limit, orderId);
    }
}
