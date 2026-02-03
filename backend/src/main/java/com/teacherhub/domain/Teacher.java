package com.teacherhub.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 강사 정보
 */
@Entity
@Table(name = "teachers", indexes = {
    @Index(name = "idx_teachers_academy", columnList = "academy_id"),
    @Index(name = "idx_teachers_subject", columnList = "subject_id"),
    @Index(name = "idx_teachers_name", columnList = "name")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Teacher {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "academy_id")
    private Academy academy;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "subject_id")
    private Subject subject;

    @Column(nullable = false, length = 100)
    private String name;

    @JdbcTypeCode(SqlTypes.ARRAY)
    @Column(columnDefinition = "text[]")
    private String[] aliases;  // 별명, 이름 변형 배열

    @Column(name = "profile_url", length = 300)
    private String profileUrl;

    @Column(name = "is_active")
    @Builder.Default
    private Boolean isActive = true;

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", insertable = false, updatable = false)
    private LocalDateTime updatedAt;

    // Relationships
    @OneToMany(mappedBy = "teacher")
    private List<TeacherMention> mentions;

    @OneToMany(mappedBy = "teacher")
    private List<DailyReport> dailyReports;

    /**
     * 강사 이름과 모든 별명 반환
     */
    public List<String> getAllNames() {
        List<String> names = new ArrayList<>();
        names.add(this.name);
        if (this.aliases != null) {
            for (String alias : this.aliases) {
                names.add(alias);
            }
        }
        return names;
    }
}
