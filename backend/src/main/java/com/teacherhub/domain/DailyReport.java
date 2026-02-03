package com.teacherhub.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 강사별 데일리 리포트
 */
@Entity
@Table(name = "daily_reports",
    uniqueConstraints = {
        @UniqueConstraint(name = "uq_reports_date_teacher", columnNames = {"report_date", "teacher_id"})
    },
    indexes = {
        @Index(name = "idx_reports_date", columnList = "report_date"),
        @Index(name = "idx_reports_teacher", columnList = "teacher_id")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DailyReport {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "report_date", nullable = false)
    private LocalDate reportDate;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "teacher_id")
    private Teacher teacher;

    // 집계 데이터
    @Column(name = "mention_count")
    @Builder.Default
    private Integer mentionCount = 0;

    @Column(name = "post_mention_count")
    @Builder.Default
    private Integer postMentionCount = 0;

    @Column(name = "comment_mention_count")
    @Builder.Default
    private Integer commentMentionCount = 0;

    // 감성 분석 집계
    @Column(name = "positive_count")
    @Builder.Default
    private Integer positiveCount = 0;

    @Column(name = "negative_count")
    @Builder.Default
    private Integer negativeCount = 0;

    @Column(name = "neutral_count")
    @Builder.Default
    private Integer neutralCount = 0;

    @Column(name = "avg_sentiment_score")
    private Double avgSentimentScore;

    // 난이도 집계
    @Column(name = "difficulty_easy_count")
    @Builder.Default
    private Integer difficultyEasyCount = 0;

    @Column(name = "difficulty_medium_count")
    @Builder.Default
    private Integer difficultyMediumCount = 0;

    @Column(name = "difficulty_hard_count")
    @Builder.Default
    private Integer difficultyHardCount = 0;

    // 추천 집계
    @Column(name = "recommendation_count")
    @Builder.Default
    private Integer recommendationCount = 0;

    // 전일 대비 변화
    @Column(name = "mention_change")
    @Builder.Default
    private Integer mentionChange = 0;

    @Column(name = "sentiment_change")
    private Double sentimentChange;

    // AI 요약
    @Column(columnDefinition = "TEXT")
    private String summary;

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(name = "top_keywords", columnDefinition = "text[]")
    private String[] topKeywords;

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;
}
