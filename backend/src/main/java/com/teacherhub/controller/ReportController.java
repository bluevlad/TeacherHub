package com.teacherhub.controller;

import com.teacherhub.domain.DailyReport;
import com.teacherhub.dto.PeriodReportDTO;
import com.teacherhub.repository.DailyReportRepository;
import com.teacherhub.service.ReportService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.temporal.WeekFields;
import java.util.*;

/**
 * 기간별 리포트 API Controller
 * 일별/주별/월별 데이터 조회
 */
@RestController
@RequestMapping("/api/v2/reports")
@RequiredArgsConstructor
@Validated
@Slf4j
public class ReportController {

    private final DailyReportRepository dailyReportRepository;
    private final ReportService reportService;

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
        List<DailyReport> reports = dailyReportRepository.findByReportDateWithTeacher(reportDate);

        PeriodReportDTO result = reportService.buildPeriodReport(
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
            @RequestParam(required = false) @Min(2000) @Max(2100) Integer year,
            @RequestParam(required = false) @Min(1) @Max(53) Integer week) {

        LocalDate today = LocalDate.now();
        int targetYear = year != null ? year : today.getYear();
        int targetWeek = week != null ? week : today.get(WEEK_FIELDS.weekOfWeekBasedYear());

        // 주차의 시작일과 종료일 계산
        LocalDate weekStart = reportService.getWeekStartDate(targetYear, targetWeek);
        LocalDate weekEnd = weekStart.plusDays(6);

        // 해당 기간의 일별 리포트 조회 (단일 범위 쿼리 + JOIN FETCH)
        List<DailyReport> allReports = dailyReportRepository.findByReportDateBetweenWithTeacher(weekStart, weekEnd);

        PeriodReportDTO result = reportService.buildPeriodReport(
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
            @RequestParam(required = false) @Min(2000) @Max(2100) Integer year,
            @RequestParam(required = false) @Min(1) @Max(12) Integer month) {

        LocalDate today = LocalDate.now();
        int targetYear = year != null ? year : today.getYear();
        int targetMonth = month != null ? month : today.getMonthValue();

        LocalDate monthStart = LocalDate.of(targetYear, targetMonth, 1);
        LocalDate monthEnd = monthStart.plusMonths(1).minusDays(1);

        // 해당 월의 일별 리포트 조회 (단일 범위 쿼리 + JOIN FETCH)
        List<DailyReport> allReports = dailyReportRepository.findByReportDateBetweenWithTeacher(monthStart, monthEnd);

        PeriodReportDTO result = reportService.buildPeriodReport(
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
                    reportService.getDayOfWeekKorean(date.getDayOfWeek())));
            dailyOptions.add(option);
        }
        periods.put("daily", dailyOptions);

        // 주별 - 현재 연도 주차
        List<Map<String, Object>> weeklyOptions = new ArrayList<>();
        int currentWeek = today.get(WEEK_FIELDS.weekOfWeekBasedYear());
        for (int week = 1; week <= currentWeek; week++) {
            LocalDate weekStart = reportService.getWeekStartDate(currentYear, week);
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
}
