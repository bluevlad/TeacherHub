package com.teacherhub.controller;

import com.teacherhub.domain.DailyReport;
import com.teacherhub.dto.DailyReportDTO;
import com.teacherhub.dto.PeriodReportDTO;
import com.teacherhub.dto.PeriodSummaryDTO;
import com.teacherhub.repository.DailyReportRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.temporal.WeekFields;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 기간별 리포트 API Controller
 * 일별/주별/월별 데이터 조회
 */
@RestController
@RequestMapping("/api/v2/reports")
@RequiredArgsConstructor
@CrossOrigin(origins = {"${app.cors.allowed-origins:http://localhost:3000}"})
@Slf4j
public class ReportController {

    private final DailyReportRepository dailyReportRepository;

    // 한국 주차 기준 (월요일 시작)
    private static final WeekFields WEEK_FIELDS = WeekFields.of(DayOfWeek.MONDAY, 4);

    /**
     * 일별 리포트 조회
     * GET /api/v2/reports/daily?date=2026-02-04
     */
    @GetMapping("/daily")
    public ResponseEntity<PeriodReportDTO> getDailyReport(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {

        LocalDate reportDate = date != null ? date : LocalDate.now();
        List<DailyReport> reports = dailyReportRepository.findByReportDate(reportDate);

        PeriodReportDTO result = buildPeriodReport(
                "daily",
                reportDate,
                reportDate,
                reports
        );

        return ResponseEntity.ok(result);
    }

    /**
     * 주별 리포트 조회
     * GET /api/v2/reports/weekly?year=2026&week=5
     */
    @GetMapping("/weekly")
    public ResponseEntity<PeriodReportDTO> getWeeklyReport(
            @RequestParam(required = false) Integer year,
            @RequestParam(required = false) Integer week) {

        LocalDate today = LocalDate.now();
        int targetYear = year != null ? year : today.getYear();
        int targetWeek = week != null ? week : today.get(WEEK_FIELDS.weekOfWeekBasedYear());

        // 주차의 시작일과 종료일 계산
        LocalDate weekStart = getWeekStartDate(targetYear, targetWeek);
        LocalDate weekEnd = weekStart.plusDays(6);

        // 해당 기간의 일별 리포트 조회
        List<DailyReport> allReports = new ArrayList<>();
        LocalDate current = weekStart;
        while (!current.isAfter(weekEnd)) {
            allReports.addAll(dailyReportRepository.findByReportDate(current));
            current = current.plusDays(1);
        }

        PeriodReportDTO result = buildPeriodReport(
                "weekly",
                weekStart,
                weekEnd,
                allReports
        );
        result.setYear(targetYear);
        result.setWeek(targetWeek);
        result.setPeriodLabel(String.format("%d년 %d월 %d주차", targetYear, weekStart.getMonthValue(), targetWeek));

        return ResponseEntity.ok(result);
    }

    /**
     * 월별 리포트 조회
     * GET /api/v2/reports/monthly?year=2026&month=1
     */
    @GetMapping("/monthly")
    public ResponseEntity<PeriodReportDTO> getMonthlyReport(
            @RequestParam(required = false) Integer year,
            @RequestParam(required = false) Integer month) {

        LocalDate today = LocalDate.now();
        int targetYear = year != null ? year : today.getYear();
        int targetMonth = month != null ? month : today.getMonthValue();

        LocalDate monthStart = LocalDate.of(targetYear, targetMonth, 1);
        LocalDate monthEnd = monthStart.plusMonths(1).minusDays(1);

        // 해당 월의 일별 리포트 조회
        List<DailyReport> allReports = new ArrayList<>();
        LocalDate current = monthStart;
        while (!current.isAfter(monthEnd)) {
            allReports.addAll(dailyReportRepository.findByReportDate(current));
            current = current.plusDays(1);
        }

        PeriodReportDTO result = buildPeriodReport(
                "monthly",
                monthStart,
                monthEnd,
                allReports
        );
        result.setYear(targetYear);
        result.setMonth(targetMonth);
        result.setPeriodLabel(String.format("%d년 %d월", targetYear, targetMonth));

        return ResponseEntity.ok(result);
    }

    /**
     * 선택 가능한 기간 목록 조회
     * GET /api/v2/reports/periods
     */
    @GetMapping("/periods")
    public ResponseEntity<Map<String, Object>> getAvailablePeriods() {
        LocalDate today = LocalDate.now();
        int currentYear = today.getYear();

        Map<String, Object> periods = new HashMap<>();

        // 일별 - 최근 30일
        List<Map<String, Object>> dailyOptions = new ArrayList<>();
        for (int i = 0; i < 30; i++) {
            LocalDate date = today.minusDays(i);
            Map<String, Object> option = new HashMap<>();
            option.put("date", date.toString());
            option.put("label", String.format("%d월 %d일 (%s)",
                    date.getMonthValue(), date.getDayOfMonth(),
                    getDayOfWeekKorean(date.getDayOfWeek())));
            dailyOptions.add(option);
        }
        periods.put("daily", dailyOptions);

        // 주별 - 현재 연도 주차
        List<Map<String, Object>> weeklyOptions = new ArrayList<>();
        int currentWeek = today.get(WEEK_FIELDS.weekOfWeekBasedYear());
        for (int week = 1; week <= currentWeek; week++) {
            LocalDate weekStart = getWeekStartDate(currentYear, week);
            LocalDate weekEnd = weekStart.plusDays(6);
            Map<String, Object> option = new HashMap<>();
            option.put("year", currentYear);
            option.put("week", week);
            option.put("label", String.format("%d월 %d주차 (%d/%d~%d/%d)",
                    weekStart.getMonthValue(), week,
                    weekStart.getMonthValue(), weekStart.getDayOfMonth(),
                    weekEnd.getMonthValue(), weekEnd.getDayOfMonth()));
            option.put("startDate", weekStart.toString());
            option.put("endDate", weekEnd.toString());
            weeklyOptions.add(option);
        }
        Collections.reverse(weeklyOptions); // 최신순
        periods.put("weekly", weeklyOptions);

        // 월별 - 현재 연도
        List<Map<String, Object>> monthlyOptions = new ArrayList<>();
        int currentMonth = today.getMonthValue();
        for (int month = currentMonth; month >= 1; month--) {
            Map<String, Object> option = new HashMap<>();
            option.put("year", currentYear);
            option.put("month", month);
            option.put("label", String.format("%d년 %d월", currentYear, month));
            monthlyOptions.add(option);
        }
        periods.put("monthly", monthlyOptions);

        // 현재 기준 정보
        Map<String, Object> current = new HashMap<>();
        current.put("year", currentYear);
        current.put("month", currentMonth);
        current.put("week", currentWeek);
        current.put("date", today.toString());
        periods.put("current", current);

        return ResponseEntity.ok(periods);
    }

    /**
     * 기간 리포트 생성 (강사별 집계)
     */
    private PeriodReportDTO buildPeriodReport(String periodType, LocalDate startDate,
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
    private PeriodSummaryDTO aggregateTeacherReports(Long teacherId, List<DailyReport> reports) {
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
    private LocalDate getWeekStartDate(int year, int week) {
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
    private String getDayOfWeekKorean(DayOfWeek dow) {
        switch (dow) {
            case MONDAY: return "월";
            case TUESDAY: return "화";
            case WEDNESDAY: return "수";
            case THURSDAY: return "목";
            case FRIDAY: return "금";
            case SATURDAY: return "토";
            case SUNDAY: return "일";
            default: return "";
        }
    }
}
