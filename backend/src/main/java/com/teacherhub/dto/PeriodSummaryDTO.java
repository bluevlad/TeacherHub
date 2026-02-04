package com.teacherhub.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 강사별 기간 집계 DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PeriodSummaryDTO {

    private Long teacherId;
    private String teacherName;
    private String academyName;
    private String subjectName;

    // 멘션 통계
    private Integer mentionCount;
    private Integer positiveCount;
    private Integer negativeCount;
    private Integer neutralCount;
    private Integer recommendationCount;

    // 감성 점수
    private Double avgSentimentScore;

    // 집계 정보
    private Integer reportDays;     // 데이터가 있는 일수
}
