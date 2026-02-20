package com.teacherhub.dto;

import com.teacherhub.domain.DailyReport;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DailyReportDTO {

    private Long id;
    private LocalDate reportDate;
    private Long teacherId;
    private String teacherName;
    private String academyName;
    private String subjectName;

    // 멘션 통계
    private Integer mentionCount;
    private Integer postMentionCount;
    private Integer commentMentionCount;

    // 감성 분석
    private Integer positiveCount;
    private Integer negativeCount;
    private Integer neutralCount;
    private Double avgSentimentScore;

    // 추천
    private Integer recommendationCount;

    // 변화
    private Integer mentionChange;
    private Double sentimentChange;

    // 요약
    private String summary;

    public static DailyReportDTO fromEntity(DailyReport report) {
        if (report == null) return null;

        return DailyReportDTO.builder()
                .id(report.getId())
                .reportDate(report.getReportDate())
                .teacherId(report.getTeacher() != null ? report.getTeacher().getId() : null)
                .teacherName(report.getTeacher() != null ? report.getTeacher().getName() : null)
                .academyName(report.getTeacher() != null && report.getTeacher().getAcademy() != null
                        ? report.getTeacher().getAcademy().getName() : null)
                .subjectName(report.getTeacher() != null && report.getTeacher().getSubject() != null
                        ? report.getTeacher().getSubject().getName() : null)
                .mentionCount(report.getMentionCount())
                .postMentionCount(report.getPostMentionCount())
                .commentMentionCount(report.getCommentMentionCount())
                .positiveCount(report.getPositiveCount())
                .negativeCount(report.getNegativeCount())
                .neutralCount(report.getNeutralCount())
                .avgSentimentScore(report.getAvgSentimentScore())
                .recommendationCount(report.getRecommendationCount())
                .mentionChange(report.getMentionChange())
                .sentimentChange(report.getSentimentChange())
                .summary(report.getSummary())
                .build();
    }
}
