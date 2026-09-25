package com.olwethu.ecommerce.api;

import com.olwethu.ecommerce.service.MetadataService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/metadata")
public class MetadataController {
    private final MetadataService service;
    public MetadataController(MetadataService service) { this.service = service; }

    @GetMapping
    public Map<String, Object> metadata() {
        return service.metadata();
    }
}
