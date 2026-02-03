package com.teacherhub.dto;

import com.teacherhub.domain.Academy;
import lombok.*;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AcademyDTO {
    private Long id;
    private String code;
    private String name;
    private String website;
    private String logoUrl;
    private Boolean isActive;
    private LocalDateTime createdAt;

    public static AcademyDTO fromEntity(Academy academy) {
        return AcademyDTO.builder()
                .id(academy.getId())
                .code(academy.getCode())
                .name(academy.getName())
                .website(academy.getWebsite())
                .logoUrl(academy.getLogoUrl())
                .isActive(academy.getIsActive())
                .createdAt(academy.getCreatedAt())
                .build();
    }
}
