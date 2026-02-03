package com.teacherhub.dto;

import com.teacherhub.domain.Teacher;
import lombok.*;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TeacherDTO {
    private Long id;
    private String name;
    private String[] aliases;
    private Long academyId;
    private String academyName;
    private Long subjectId;
    private String subjectName;
    private String profileUrl;
    private Boolean isActive;
    private LocalDateTime createdAt;

    public static TeacherDTO fromEntity(Teacher teacher) {
        return TeacherDTO.builder()
                .id(teacher.getId())
                .name(teacher.getName())
                .aliases(teacher.getAliases())
                .academyId(teacher.getAcademy() != null ? teacher.getAcademy().getId() : null)
                .academyName(teacher.getAcademy() != null ? teacher.getAcademy().getName() : null)
                .subjectId(teacher.getSubject() != null ? teacher.getSubject().getId() : null)
                .subjectName(teacher.getSubject() != null ? teacher.getSubject().getName() : null)
                .profileUrl(teacher.getProfileUrl())
                .isActive(teacher.getIsActive())
                .createdAt(teacher.getCreatedAt())
                .build();
    }
}
