package com.olwethu.ecommerce.api;

import com.olwethu.ecommerce.api.dto.OrderLineResponse;
import com.olwethu.ecommerce.service.OrderService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/orders")
@Validated
public class OrderController {
    private final OrderService service;
    public OrderController(OrderService service) { this.service = service; }

    @GetMapping("/lines")
    public List<OrderLineResponse> findOrderLines(
            @RequestParam(defaultValue = "50") @Min(1) @Max(200) int limit,
            @RequestParam(defaultValue = "") String orderId) {
        return service.findOrderLines(limit, orderId);
    }
}
