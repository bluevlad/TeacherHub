package com.teacherhub.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;

/**
 * 크롤링 작업 로그
 */
@Entity
@Table(name = "crawl_logs")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CrawlLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "source_id")
    private CollectionSource source;

    @Column(name = "started_at", nullable = false)
    private LocalDateTime startedAt;

    @Column(name = "finished_at")
    private LocalDateTime finishedAt;

    @Column(nullable = false, length = 20)
    private String status;  // running, completed, failed

    @Column(name = "posts_collected")
    @Builder.Default
    private Integer postsCollected = 0;

    @Column(name = "comments_collected")
    @Builder.Default
    private Integer commentsCollected = 0;

    @Column(name = "mentions_found")
    @Builder.Default
    private Integer mentionsFound = 0;

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;
}
