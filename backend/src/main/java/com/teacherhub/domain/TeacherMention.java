package com.teacherhub.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;

/**
 * 강사 멘션 및 분석 결과
 */
@Entity
@Table(name = "teacher_mentions",
    uniqueConstraints = {
        @UniqueConstraint(name = "uq_mentions_teacher_post_comment_type",
            columnNames = {"teacher_id", "post_id", "comment_id", "mention_type"})
    },
    indexes = {
        @Index(name = "idx_mentions_teacher", columnList = "teacher_id"),
        @Index(name = "idx_mentions_post", columnList = "post_id"),
        @Index(name = "idx_mentions_analyzed", columnList = "analyzed_at")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TeacherMention {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "teacher_id")
    private Teacher teacher;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "post_id")
    private Post post;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "comment_id")
    private Comment comment;

    @Column(name = "mention_type", nullable = false, length = 20)
    private String mentionType;  // title, content, comment

    @Column(name = "matched_text", length = 200)
    private String matchedText;  // 매칭된 텍스트

    @Column(columnDefinition = "TEXT")
    private String context;  // 주변 문맥 (앞뒤 100자)

    // 분석 결과
    @Column(length = 20)
    private String sentiment;  // POSITIVE, NEGATIVE, NEUTRAL

    @Column(name = "sentiment_score")
    private Double sentimentScore;  // -1.0 ~ 1.0

    @Column(length = 20)
    private String difficulty;  // EASY, MEDIUM, HARD

    @Column(name = "is_recommended")
    private Boolean isRecommended;

    @Column(name = "analyzed_at", insertable = false, updatable = false)
    private LocalDateTime analyzedAt;
}
