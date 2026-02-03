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
 * 공무원 학원 정보
 */
@Entity
@Table(name = "academies")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Academy {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(unique = true, nullable = false, length = 50)
    private String code;  // gongdangi, hackers, willbes, eduwill

    @Column(length = 200)
    private String website;

    @Column(name = "logo_url", length = 300)
    private String logoUrl;

    @Column(name = "is_active")
    @Builder.Default
    private Boolean isActive = true;

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", insertable = false, updatable = false)
    private LocalDateTime updatedAt;

    // Relationships
    @OneToMany(mappedBy = "academy")
    private List<Teacher> teachers;

    @OneToMany(mappedBy = "academy")
    private List<AcademyDailyStats> dailyStats;
}
