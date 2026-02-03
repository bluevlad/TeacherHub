package com.teacherhub.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 수집된 게시글
 */
@Entity
@Table(name = "posts",
    uniqueConstraints = {
        @UniqueConstraint(name = "uq_posts_source_external", columnNames = {"source_id", "external_id"})
    },
    indexes = {
        @Index(name = "idx_posts_source", columnList = "source_id"),
        @Index(name = "idx_posts_date", columnList = "post_date"),
        @Index(name = "idx_posts_collected", columnList = "collected_at")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Post {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "source_id")
    private CollectionSource source;

    @Column(name = "external_id", length = 100)
    private String externalId;  // 원본 게시글 ID

    @Column(nullable = false, length = 500)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String content;

    @Column(length = 500)
    private String url;

    @Column(length = 100)
    private String author;

    @Column(name = "post_date")
    private LocalDateTime postDate;

    @Column(name = "view_count")
    @Builder.Default
    private Integer viewCount = 0;

    @Column(name = "like_count")
    @Builder.Default
    private Integer likeCount = 0;

    @Column(name = "comment_count")
    @Builder.Default
    private Integer commentCount = 0;

    @Column(name = "collected_at", insertable = false, updatable = false)
    private LocalDateTime collectedAt;

    // Relationships
    @OneToMany(mappedBy = "post", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Comment> comments;

    @OneToMany(mappedBy = "post", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<TeacherMention> mentions;
}
