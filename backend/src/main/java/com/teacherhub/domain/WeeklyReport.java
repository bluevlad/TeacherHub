package com.teacherhub.domain;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 주간 리포트 엔티티
 */
@Entity
@Table(name = "weekly_reports",
    uniqueConstraints = @UniqueConstraint(
        name = "uk_weekly_teacher_year_week",
        columnNames = {"teacher_id", "year", "week_number"}
    ),
    indexes = {
        @Index(name = "idx_weekly_reports_teacher", columnList = "teacher_id"),
        @Index(name = "idx_weekly_reports_academy", columnList = "academy_id"),
        @Index(name = "idx_weekly_reports_year_week", columnList = "year, week_number")
    }
)
@Getter @Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WeeklyReport {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "teacher_id", nullable = false)
    private Teacher teacher;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "academy_id", nullable = false)
    private Academy academy;

    // 기간 정보
    @Column(name = "year", nullable = false)
    private Integer year;

    @Column(name = "week_number", nullable = false)
    private Integer weekNumber;

    @Column(name = "week_start_date", nullable = false)
    private LocalDate weekStartDate;

    @Column(name = "week_end_date", nullable = false)
    private LocalDate weekEndDate;

    // 언급 통계
    @Column(name = "mention_count")
    @Builder.Default
    private Integer mentionCount = 0;

    @Column(name = "positive_count")
    @Builder.Default
    private Integer positiveCount = 0;

    @Column(name = "negative_count")
    @Builder.Default
    private Integer negativeCount = 0;

    @Column(name = "neutral_count")
    @Builder.Default
    private Integer neutralCount = 0;

    @Column(name = "recommendation_count")
    @Builder.Default
    private Integer recommendationCount = 0;

    // 난이도 통계
    @Column(name = "difficulty_easy_count")
    @Builder.Default
    private Integer difficultyEasyCount = 0;

    @Column(name = "difficulty_medium_count")
    @Builder.Default
    private Integer difficultyMediumCount = 0;

    @Column(name = "difficulty_hard_count")
    @Builder.Default
    private Integer difficultyHardCount = 0;

    // 계산 지표
    @Column(name = "avg_sentiment_score", precision = 5, scale = 4)
    private BigDecimal avgSentimentScore;

    @Column(name = "sentiment_trend", precision = 5, scale = 4)
    private BigDecimal sentimentTrend;

    @Column(name = "mention_change_rate", precision = 6, scale = 2)
    private BigDecimal mentionChangeRate;

    @Column(name = "weekly_rank")
    private Integer weeklyRank;

    @Column(name = "academy_rank")
    private Integer academyRank;

    // 분석 데이터 (JSON)
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "top_keywords", columnDefinition = "jsonb")
    private List<String> topKeywords;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "source_distribution", columnDefinition = "jsonb")
    private Map<String, Integer> sourceDistribution;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "daily_distribution", columnDefinition = "jsonb")
    private Map<String, Integer> dailyDistribution;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "mention_types", columnDefinition = "jsonb")
    private Map<String, Integer> mentionTypes;

    // AI 요약
    @Column(name = "ai_summary", columnDefinition = "TEXT")
    private String aiSummary;

    @Column(name = "highlight_positive", columnDefinition = "TEXT")
    private String highlightPositive;

    @Column(name = "highlight_negative", columnDefinition = "TEXT")
    private String highlightNegative;

    // 메타데이터
    @Column(name = "is_complete")
    @Builder.Default
    private Boolean isComplete = false;

    @Column(name = "aggregated_at")
    private LocalDateTime aggregatedAt;

    @Column(name = "created_at")
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "updated_at")
    @Builder.Default
    private LocalDateTime updatedAt = LocalDateTime.now();

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
