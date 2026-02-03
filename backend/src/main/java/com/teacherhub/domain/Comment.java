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
 * 게시글 댓글
 */
@Entity
@Table(name = "comments", indexes = {
    @Index(name = "idx_comments_post", columnList = "post_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Comment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "post_id")
    private Post post;

    @Column(name = "external_id", length = 100)
    private String externalId;

    @Column(columnDefinition = "TEXT")
    private String content;

    @Column(length = 100)
    private String author;

    @Column(name = "comment_date")
    private LocalDateTime commentDate;

    @Column(name = "like_count")
    @Builder.Default
    private Integer likeCount = 0;

    @Column(name = "collected_at", insertable = false, updatable = false)
    private LocalDateTime collectedAt;

    // Relationships
    @OneToMany(mappedBy = "comment", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<TeacherMention> mentions;
}
