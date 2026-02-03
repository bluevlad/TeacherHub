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
 * 학원별 주간 통계 엔티티
 */
@Entity
@Table(name = "academy_weekly_stats",
    uniqueConstraints = @UniqueConstraint(
        name = "uk_academy_weekly_year_week",
        columnNames = {"academy_id", "year", "week_number"}
    )
)
@Getter @Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AcademyWeeklyStats {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

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

    // 통계
    @Column(name = "total_mentions")
    @Builder.Default
    private Integer totalMentions = 0;

    @Column(name = "total_teachers_mentioned")
    @Builder.Default
    private Integer totalTeachersMentioned = 0;

    @Column(name = "avg_sentiment_score", precision = 5, scale = 4)
    private BigDecimal avgSentimentScore;

    @Column(name = "total_positive")
    @Builder.Default
    private Integer totalPositive = 0;

    @Column(name = "total_negative")
    @Builder.Default
    private Integer totalNegative = 0;

    @Column(name = "total_recommendations")
    @Builder.Default
    private Integer totalRecommendations = 0;

    // 랭킹 정보
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "top_teacher_id")
    private Teacher topTeacher;

    @Column(name = "top_teacher_mentions")
    @Builder.Default
    private Integer topTeacherMentions = 0;

    // 분석 데이터
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "top_keywords", columnDefinition = "jsonb")
    private List<String> topKeywords;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "source_distribution", columnDefinition = "jsonb")
    private Map<String, Integer> sourceDistribution;

    // 메타데이터
    @Column(name = "aggregated_at")
    private LocalDateTime aggregatedAt;

    @Column(name = "created_at")
    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
}
