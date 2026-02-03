package com.teacherhub.dto;

import lombok.*;

import java.math.BigDecimal;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WeeklySummaryDTO {
    private Integer year;
    private Integer weekNumber;
    private String weekLabel;

    private Integer totalMentions;
    private Integer totalPositive;
    private Integer totalNegative;
    private Integer totalRecommendations;
    private Integer totalTeachers;
    private Integer totalAcademies;

    private BigDecimal avgSentimentScore;
    private BigDecimal mentionChangeRate;
}
