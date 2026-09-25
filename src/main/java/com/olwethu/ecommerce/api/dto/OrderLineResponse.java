package com.olwethu.ecommerce.api.dto;

import java.math.BigDecimal;

public record OrderLineResponse(
        long factOrderSalesId, String orderId, int orderDateKey, int shipDateKey,
        String customerKey, String productKey, String locationKey, String shipModeKey,
        String salesTargetKey, int quantity, BigDecimal sales, BigDecimal profit,
        BigDecimal discount) {}
