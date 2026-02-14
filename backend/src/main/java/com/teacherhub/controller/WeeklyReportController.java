package com.teacherhub.controller;

import com.teacherhub.dto.WeeklyReportDTO;
import com.teacherhub.dto.WeeklySummaryDTO;
import com.teacherhub.service.WeeklyReportService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 주간 리포트 API Controller
 */
@RestController
@RequestMapping("/api/v2/weekly")
@RequiredArgsConstructor
@CrossOrigin(origins = {"${app.cors.allowed-origins:http://localhost:3000}"})
public class WeeklyReportController {

    private final WeeklyReportService weeklyReportService;

    /**
     * 주간 리포트 목록 조회
     * GET /api/v2/weekly/report?year=2026&week=5
     */
    @GetMapping("/report")
    public ResponseEntity<List<WeeklyReportDTO>> getWeeklyReports(
            @RequestParam Integer year,
            @RequestParam Integer week) {
        List<WeeklyReportDTO> reports = weeklyReportService.getWeeklyReports(year, week);
        return ResponseEntity.ok(reports);
    }

    /**
     * 강사별 주간 리포트 조회
     * GET /api/v2/weekly/teacher/{teacherId}?year=2026&week=5
     */
    @GetMapping("/teacher/{teacherId}")
    public ResponseEntity<WeeklyReportDTO> getTeacherWeeklyReport(
            @PathVariable Long teacherId,
            @RequestParam Integer year,
            @RequestParam Integer week) {
        return weeklyReportService.getTeacherWeeklyReport(teacherId, year, week)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * 주간 랭킹 조회
     * GET /api/v2/weekly/ranking?year=2026&week=5&limit=20
     */
    @GetMapping("/ranking")
    public ResponseEntity<List<WeeklyReportDTO>> getWeeklyRanking(
            @RequestParam Integer year,
            @RequestParam Integer week,
            @RequestParam(defaultValue = "20") Integer limit) {
        List<WeeklyReportDTO> ranking = weeklyReportService.getWeeklyRanking(year, week, limit);
        return ResponseEntity.ok(ranking);
    }

    /**
     * 학원별 주간 통계 조회
     * GET /api/v2/weekly/academy/{academyId}?year=2026&week=5
     */
    @GetMapping("/academy/{academyId}")
    public ResponseEntity<List<WeeklyReportDTO>> getAcademyWeeklyReports(
            @PathVariable Long academyId,
            @RequestParam Integer year,
            @RequestParam Integer week) {
        List<WeeklyReportDTO> reports = weeklyReportService.getAcademyWeeklyReports(academyId, year, week);
        return ResponseEntity.ok(reports);
    }

    /**
     * 강사 트렌드 조회 (최근 N주)
     * GET /api/v2/weekly/teacher/{teacherId}/trend?weeks=8
     */
    @GetMapping("/teacher/{teacherId}/trend")
    public ResponseEntity<List<WeeklyReportDTO>> getTeacherTrend(
            @PathVariable Long teacherId,
            @RequestParam(defaultValue = "8") Integer weeks) {
        List<WeeklyReportDTO> trend = weeklyReportService.getTeacherTrend(teacherId, weeks);
        return ResponseEntity.ok(trend);
    }

    /**
     * 학원 트렌드 조회 (최근 N주)
     * GET /api/v2/weekly/academy/{academyId}/trend?weeks=8
     */
    @GetMapping("/academy/{academyId}/trend")
    public ResponseEntity<List<WeeklyReportDTO>> getAcademyTrend(
            @PathVariable Long academyId,
            @RequestParam(defaultValue = "8") Integer weeks) {
        List<WeeklyReportDTO> trend = weeklyReportService.getAcademyTrend(academyId, weeks);
        return ResponseEntity.ok(trend);
    }

    /**
     * 현재 주차 정보 조회
     * GET /api/v2/weekly/current
     */
    @GetMapping("/current")
    public ResponseEntity<Map<String, Object>> getCurrentWeek() {
        Map<String, Object> weekInfo = weeklyReportService.getCurrentWeekInfo();
        return ResponseEntity.ok(weekInfo);
    }

    /**
     * 주간 요약 통계 조회
     * GET /api/v2/weekly/summary?year=2026&week=5
     */
    @GetMapping("/summary")
    public ResponseEntity<WeeklySummaryDTO> getWeeklySummary(
            @RequestParam Integer year,
            @RequestParam Integer week) {
        WeeklySummaryDTO summary = weeklyReportService.getWeeklySummary(year, week);
        return ResponseEntity.ok(summary);
    }
}
