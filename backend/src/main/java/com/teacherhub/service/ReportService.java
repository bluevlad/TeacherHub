package com.teacherhub.service;

import com.teacherhub.domain.DailyReport;
import com.teacherhub.dto.PeriodReportDTO;
import com.teacherhub.dto.PeriodSummaryDTO;
import org.springframework.stereotype.Service;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 기간별 리포트 비즈니스 로직 서비스
 * ReportController에서 분리된 집계/변환 로직 담당
 */
@Service
public class ReportService {

    /**
     * 기간 리포트 생성 (강사별 집계)
     */
    public PeriodReportDTO buildPeriodReport(String periodType, LocalDate startDate,
                                              LocalDate endDate, List<DailyReport> reports) {
        // 강사별 집계
        Map<Long, List<DailyReport>> byTeacher = reports.stream()
                .filter(r -> r.getTeacher() != null)
                .collect(Collectors.groupingBy(r -> r.getTeacher().getId()));

        List<PeriodSummaryDTO> teacherSummaries = byTeacher.entrySet().stream()
                .map(entry -> aggregateTeacherReports(entry.getKey(), entry.getValue()))
                .sorted((a, b) -> Integer.compare(b.getMentionCount(), a.getMentionCount()))
                .collect(Collectors.toList());

        // 전체 통계
        int totalMentions = teacherSummaries.stream().mapToInt(PeriodSummaryDTO::getMentionCount).sum();
        int totalPositive = teacherSummaries.stream().mapToInt(PeriodSummaryDTO::getPositiveCount).sum();
        int totalNegative = teacherSummaries.stream().mapToInt(PeriodSummaryDTO::getNegativeCount).sum();
        int totalNeutral = teacherSummaries.stream().mapToInt(PeriodSummaryDTO::getNeutralCount).sum();

        double avgSentiment = teacherSummaries.stream()
                .filter(s -> s.getAvgSentimentScore() != null)
                .mapToDouble(PeriodSummaryDTO::getAvgSentimentScore)
                .average()
                .orElse(0.0);

        return PeriodReportDTO.builder()
                .periodType(periodType)
                .startDate(startDate)
                .endDate(endDate)
                .totalTeachers(teacherSummaries.size())
                .totalMentions(totalMentions)
                .totalPositive(totalPositive)
                .totalNegative(totalNegative)
                .totalNeutral(totalNeutral)
                .avgSentimentScore(Math.round(avgSentiment * 100.0) / 100.0)
                .positiveRatio(totalMentions > 0 ? Math.round(totalPositive * 100.0 / totalMentions) : 0)
                .teacherSummaries(teacherSummaries)
                .build();
    }

    /**
     * 강사별 리포트 집계
     */
    public PeriodSummaryDTO aggregateTeacherReports(Long teacherId, List<DailyReport> reports) {
        DailyReport first = reports.get(0);

        int mentionCount = reports.stream().mapToInt(r -> r.getMentionCount() != null ? r.getMentionCount() : 0).sum();
        int positiveCount = reports.stream().mapToInt(r -> r.getPositiveCount() != null ? r.getPositiveCount() : 0).sum();
        int negativeCount = reports.stream().mapToInt(r -> r.getNegativeCount() != null ? r.getNegativeCount() : 0).sum();
        int neutralCount = reports.stream().mapToInt(r -> r.getNeutralCount() != null ? r.getNeutralCount() : 0).sum();
        int recommendationCount = reports.stream().mapToInt(r -> r.getRecommendationCount() != null ? r.getRecommendationCount() : 0).sum();

        double avgSentiment = reports.stream()
                .filter(r -> r.getAvgSentimentScore() != null)
                .mapToDouble(DailyReport::getAvgSentimentScore)
                .average()
                .orElse(0.0);

        return PeriodSummaryDTO.builder()
                .teacherId(teacherId)
                .teacherName(first.getTeacher() != null ? first.getTeacher().getName() : "Unknown")
                .academyName(first.getTeacher() != null && first.getTeacher().getAcademy() != null
                        ? first.getTeacher().getAcademy().getName() : null)
                .subjectName(first.getTeacher() != null && first.getTeacher().getSubject() != null
                        ? first.getTeacher().getSubject().getName() : null)
                .mentionCount(mentionCount)
                .positiveCount(positiveCount)
                .negativeCount(negativeCount)
                .neutralCount(neutralCount)
                .recommendationCount(recommendationCount)
                .avgSentimentScore(Math.round(avgSentiment * 100.0) / 100.0)
                .reportDays(reports.size())
                .build();
    }

    /**
     * 주차 시작일 계산 (월요일)
     */
    public LocalDate getWeekStartDate(int year, int week) {
        // 해당 연도 1월 1일
        LocalDate jan1 = LocalDate.of(year, 1, 1);

        // 1월 1일이 속한 주의 월요일
        LocalDate firstMonday = jan1.with(DayOfWeek.MONDAY);
        if (jan1.getDayOfWeek().getValue() > DayOfWeek.THURSDAY.getValue()) {
            // 1월 1일이 금/토/일이면 다음 주 월요일이 1주차
            firstMonday = firstMonday.plusWeeks(1);
        }

        // 원하는 주차의 월요일
        return firstMonday.plusWeeks(week - 1);
    }

    /**
     * 요일 한글 변환
     */
    public String getDayOfWeekKorean(DayOfWeek dow) {
        return switch (dow) {
            case MONDAY -> "월";
            case TUESDAY -> "화";
            case WEDNESDAY -> "수";
            case THURSDAY -> "목";
            case FRIDAY -> "금";
            case SATURDAY -> "토";
            case SUNDAY -> "일";
        };
    }
}
