package com.olwethu.ecommerce.api;

import com.olwethu.ecommerce.api.dto.CustomerResponse;
import com.olwethu.ecommerce.service.CustomerService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/customers")
@Validated
public class CustomerController {
    private final CustomerService service;
    public CustomerController(CustomerService service) { this.service = service; }

    @GetMapping
    public List<CustomerResponse> findCustomers(
            @RequestParam(defaultValue = "50") @Min(1) @Max(200) int limit,
            @RequestParam(defaultValue = "") String segment) {
        return service.findCustomers(limit, segment);
    }
}
