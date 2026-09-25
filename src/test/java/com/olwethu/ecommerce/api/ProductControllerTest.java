package com.olwethu.ecommerce.api;

import com.olwethu.ecommerce.api.dto.ProductResponse;
import com.olwethu.ecommerce.service.ProductService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ProductController.class)
class ProductControllerTest {
    @Autowired MockMvc mvc;
    @MockBean ProductService service;

    @Test
    void productsEndpointReturnsOk() throws Exception {
        when(service.findProducts(anyInt(), anyString()))
                .thenReturn(List.of(new ProductResponse("k", "Product", "Category", "Sub")));

        mvc.perform(get("/api/v1/products"))
                .andExpect(status().isOk());
    }
}
