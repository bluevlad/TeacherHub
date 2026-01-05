package com.teacherhub.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import java.time.LocalDateTime;

@Entity
@Table(name = "reputation_data")
@Getter
@Setter
public class ReputationData {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String keyword;

    @Column(name = "site_name")
    private String siteName;

    private String title;

    private String url;

    private String sentiment; // POSITIVE, NEGATIVE, NEUTRAL

    private Double score;

    @Column(name = "post_date")
    private LocalDateTime postDate;

    @Column(name = "comment_count")
    private Integer commentCount;

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;
}
