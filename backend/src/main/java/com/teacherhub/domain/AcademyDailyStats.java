package com.teacherhub.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 학원별 데일리 통계
 */
@Entity
@Table(name = "academy_daily_stats",
    uniqueConstraints = {
        @UniqueConstraint(name = "uq_academy_stats_date_academy", columnNames = {"report_date", "academy_id"})
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AcademyDailyStats {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "report_date", nullable = false)
    private LocalDate reportDate;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "academy_id")
    private Academy academy;

    @Column(name = "total_mentions")
    @Builder.Default
    private Integer totalMentions = 0;

    @Column(name = "total_teachers_mentioned")
    @Builder.Default
    private Integer totalTeachersMentioned = 0;

    @Column(name = "avg_sentiment_score")
    private Double avgSentimentScore;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "top_teacher_id")
    private Teacher topTeacher;

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;
}
