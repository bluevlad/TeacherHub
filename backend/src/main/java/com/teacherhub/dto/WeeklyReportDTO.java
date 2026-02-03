package com.teacherhub.dto;

import com.teacherhub.domain.WeeklyReport;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WeeklyReportDTO {
    private Long id;
    private Long teacherId;
    private String teacherName;
    private Long academyId;
    private String academyName;

    private Integer year;
    private Integer weekNumber;
    private String weekLabel;
    private LocalDate weekStartDate;
    private LocalDate weekEndDate;

    private Integer mentionCount;
    private Integer positiveCount;
    private Integer negativeCount;
    private Integer neutralCount;
    private Integer recommendationCount;

    private BigDecimal avgSentimentScore;
    private BigDecimal mentionChangeRate;
    private Integer weeklyRank;
    private Integer academyRank;

    private List<String> topKeywords;
    private Map<String, Integer> sourceDistribution;

    public static WeeklyReportDTO fromEntity(WeeklyReport wr) {
        return WeeklyReportDTO.builder()
                .id(wr.getId())
                .teacherId(wr.getTeacher().getId())
                .teacherName(wr.getTeacher().getName())
                .academyId(wr.getAcademy().getId())
                .academyName(wr.getAcademy().getName())
                .year(wr.getYear())
                .weekNumber(wr.getWeekNumber())
                .weekLabel(wr.getYear() + "년 " + wr.getWeekNumber() + "주차")
                .weekStartDate(wr.getWeekStartDate())
                .weekEndDate(wr.getWeekEndDate())
                .mentionCount(wr.getMentionCount())
                .positiveCount(wr.getPositiveCount())
                .negativeCount(wr.getNegativeCount())
                .neutralCount(wr.getNeutralCount())
                .recommendationCount(wr.getRecommendationCount())
                .avgSentimentScore(wr.getAvgSentimentScore())
                .mentionChangeRate(wr.getMentionChangeRate())
                .weeklyRank(wr.getWeeklyRank())
                .academyRank(wr.getAcademyRank())
                .topKeywords(wr.getTopKeywords())
                .sourceDistribution(wr.getSourceDistribution())
                .build();
    }
}
