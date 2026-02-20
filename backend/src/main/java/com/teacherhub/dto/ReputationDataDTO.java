package com.teacherhub.dto;

import com.teacherhub.domain.ReputationData;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * ReputationData Entity의 응답용 DTO
 * Entity 직접 노출 방지 및 API 응답 형식 고정
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReputationDataDTO {

    private Long id;
    private String keyword;
    private String siteName;
    private String title;
    private String url;
    private String sentiment;
    private Double score;
    private LocalDateTime postDate;
    private Integer commentCount;
    private LocalDateTime createdAt;

    /**
     * Entity -> DTO 변환
     */
    public static ReputationDataDTO fromEntity(ReputationData entity) {
        return ReputationDataDTO.builder()
                .id(entity.getId())
                .keyword(entity.getKeyword())
                .siteName(entity.getSiteName())
                .title(entity.getTitle())
                .url(entity.getUrl())
                .sentiment(entity.getSentiment())
                .score(entity.getScore())
                .postDate(entity.getPostDate())
                .commentCount(entity.getCommentCount())
                .createdAt(entity.getCreatedAt())
                .build();
    }
}
