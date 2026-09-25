package com.olwethu.ecommerce.service;

import com.olwethu.ecommerce.api.dto.CustomerResponse;
import com.olwethu.ecommerce.repository.CustomerRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CustomerService {
    private final CustomerRepository repository;
    public CustomerService(CustomerRepository repository) { this.repository = repository; }
    public List<CustomerResponse> findCustomers(int limit, String segment) {
        return repository.findCustomers(limit, segment);
    }
}
