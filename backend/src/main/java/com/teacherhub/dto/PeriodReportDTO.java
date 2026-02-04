package com.teacherhub.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.List;

/**
 * 기간별 리포트 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PeriodReportDTO {

    // 기간 정보
    private String periodType;      // daily, weekly, monthly
    private LocalDate startDate;
    private LocalDate endDate;
    private String periodLabel;     // "2026년 2월 1주차"

    // 주별/월별 추가 정보
    private Integer year;
    private Integer month;
    private Integer week;

    // 전체 통계
    private Integer totalTeachers;
    private Integer totalMentions;
    private Integer totalPositive;
    private Integer totalNegative;
    private Integer totalNeutral;
    private Double avgSentimentScore;
    private Long positiveRatio;

    // 강사별 상세
    private List<PeriodSummaryDTO> teacherSummaries;
}
