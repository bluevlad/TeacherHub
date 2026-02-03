package com.teacherhub.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

/**
 * 분석용 키워드 사전
 */
@Entity
@Table(name = "analysis_keywords",
    uniqueConstraints = {
        @UniqueConstraint(name = "uq_keywords_category_keyword", columnNames = {"category", "keyword"})
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AnalysisKeyword {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    private String category;  // sentiment_positive, sentiment_negative, difficulty_easy, etc.

    @Column(nullable = false, length = 100)
    private String keyword;

    @Builder.Default
    private Double weight = 1.0;

    @Column(name = "is_active")
    @Builder.Default
    private Boolean isActive = true;
}
