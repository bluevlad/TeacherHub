package com.teacherhub.controller;

import com.teacherhub.domain.DailyReport;
import com.teacherhub.dto.DailyReportDTO;
import com.teacherhub.repository.DailyReportRepository;
import com.teacherhub.repository.TeacherMentionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 감성 분석 결과 API Controller
 */
@RestController
@RequestMapping("/api/v2/analysis")
@RequiredArgsConstructor
@CrossOrigin(origins = {"${app.cors.allowed-origins:http://localhost:3000}"})
public class AnalysisController {

    private final DailyReportRepository dailyReportRepository;
    private final TeacherMentionRepository teacherMentionRepository;

    /**
     * 오늘의 리포트 조회
     * GET /api/v2/analysis/today
     */
    @GetMapping("/today")
    public ResponseEntity<List<DailyReportDTO>> getTodayReports() {
        LocalDate today = LocalDate.now();
        List<DailyReport> reports = dailyReportRepository.findTopMentionedByDate(today);

        List<DailyReportDTO> dtos = reports.stream()
                .map(DailyReportDTO::fromEntity)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * 특정 날짜 리포트 조회
     * GET /api/v2/analysis/reports?date=2026-02-04
     */
    @GetMapping("/reports")
    public ResponseEntity<List<DailyReportDTO>> getReportsByDate(
            @RequestParam(required = false) String date) {

        LocalDate reportDate = date != null ? LocalDate.parse(date) : LocalDate.now();
        List<DailyReport> reports = dailyReportRepository.findTopMentionedByDate(reportDate);

        List<DailyReportDTO> dtos = reports.stream()
                .map(DailyReportDTO::fromEntity)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * 강사별 리포트 조회
     * GET /api/v2/analysis/teachers/{teacherId}/reports
     */
    @GetMapping("/teachers/{teacherId}/reports")
    public ResponseEntity<List<DailyReportDTO>> getTeacherReports(
            @PathVariable Long teacherId,
            @RequestParam(required = false) Integer days) {

        int daysBack = days != null ? days : 30;
        LocalDate startDate = LocalDate.now().minusDays(daysBack);

        List<DailyReport> reports = dailyReportRepository.findTeacherHistory(teacherId, startDate);

        List<DailyReportDTO> dtos = reports.stream()
                .map(DailyReportDTO::fromEntity)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * 학원별 리포트 조회
     * GET /api/v2/analysis/academies/{academyId}/reports?date=2026-02-04
     */
    @GetMapping("/academies/{academyId}/reports")
    public ResponseEntity<List<DailyReportDTO>> getAcademyReports(
            @PathVariable Long academyId,
            @RequestParam(required = false) String date) {

        LocalDate reportDate = date != null ? LocalDate.parse(date) : LocalDate.now();
        List<DailyReport> reports = dailyReportRepository.findByAcademyAndDate(academyId, reportDate);

        List<DailyReportDTO> dtos = reports.stream()
                .map(DailyReportDTO::fromEntity)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * 전체 통계 요약
     * GET /api/v2/analysis/summary
     */
    @GetMapping("/summary")
    public ResponseEntity<Map<String, Object>> getSummary() {
        LocalDate today = LocalDate.now();
        List<DailyReport> reports = dailyReportRepository.findByReportDate(today);

        int totalMentions = reports.stream().mapToInt(r -> r.getMentionCount() != null ? r.getMentionCount() : 0).sum();
        int totalPositive = reports.stream().mapToInt(r -> r.getPositiveCount() != null ? r.getPositiveCount() : 0).sum();
        int totalNegative = reports.stream().mapToInt(r -> r.getNegativeCount() != null ? r.getNegativeCount() : 0).sum();
        int totalNeutral = reports.stream().mapToInt(r -> r.getNeutralCount() != null ? r.getNeutralCount() : 0).sum();

        double avgSentiment = reports.stream()
                .filter(r -> r.getAvgSentimentScore() != null)
                .mapToDouble(DailyReport::getAvgSentimentScore)
                .average()
                .orElse(0.0);

        Map<String, Object> summary = new HashMap<>();
        summary.put("date", today);
        summary.put("totalTeachers", reports.size());
        summary.put("totalMentions", totalMentions);
        summary.put("totalPositive", totalPositive);
        summary.put("totalNegative", totalNegative);
        summary.put("totalNeutral", totalNeutral);
        summary.put("avgSentimentScore", Math.round(avgSentiment * 100.0) / 100.0);
        summary.put("positiveRatio", totalMentions > 0 ? Math.round(totalPositive * 100.0 / totalMentions) : 0);

        return ResponseEntity.ok(summary);
    }

    /**
     * 강사 랭킹 (멘션 수 기준)
     * GET /api/v2/analysis/ranking?type=mentions&limit=10
     */
    @GetMapping("/ranking")
    public ResponseEntity<List<DailyReportDTO>> getRanking(
            @RequestParam(defaultValue = "mentions") String type,
            @RequestParam(defaultValue = "10") int limit) {

        LocalDate today = LocalDate.now();
        List<DailyReport> reports = dailyReportRepository.findTopMentionedByDate(today);

        // 상위 N개만 반환
        List<DailyReportDTO> dtos = reports.stream()
                .limit(limit)
                .map(DailyReportDTO::fromEntity)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * 학원별 통계
     * GET /api/v2/analysis/academy-stats
     */
    @GetMapping("/academy-stats")
    public ResponseEntity<List<Map<String, Object>>> getAcademyStats() {
        LocalDate today = LocalDate.now();
        List<DailyReport> reports = dailyReportRepository.findByReportDate(today);

        // 학원별로 그룹핑
        Map<String, List<DailyReport>> byAcademy = reports.stream()
                .filter(r -> r.getTeacher() != null && r.getTeacher().getAcademy() != null)
                .collect(Collectors.groupingBy(r -> r.getTeacher().getAcademy().getName()));

        List<Map<String, Object>> academyStats = byAcademy.entrySet().stream()
                .map(entry -> {
                    String academyName = entry.getKey();
                    List<DailyReport> academyReports = entry.getValue();

                    int totalMentions = academyReports.stream()
                            .mapToInt(r -> r.getMentionCount() != null ? r.getMentionCount() : 0)
                            .sum();

                    double avgSentiment = academyReports.stream()
                            .filter(r -> r.getAvgSentimentScore() != null)
                            .mapToDouble(DailyReport::getAvgSentimentScore)
                            .average()
                            .orElse(0.0);

                    // TOP 강사 찾기
                    DailyReport topTeacher = academyReports.stream()
                            .max((a, b) -> Integer.compare(
                                    a.getMentionCount() != null ? a.getMentionCount() : 0,
                                    b.getMentionCount() != null ? b.getMentionCount() : 0))
                            .orElse(null);

                    Map<String, Object> stat = new HashMap<>();
                    stat.put("academyName", academyName);
                    stat.put("totalMentions", totalMentions);
                    stat.put("totalTeachersMentioned", academyReports.size());
                    stat.put("avgSentimentScore", Math.round(avgSentiment * 100.0) / 100.0);
                    stat.put("topTeacherName", topTeacher != null && topTeacher.getTeacher() != null
                            ? topTeacher.getTeacher().getName() : null);

                    return stat;
                })
                .sorted((a, b) -> Integer.compare(
                        (Integer) b.get("totalMentions"),
                        (Integer) a.get("totalMentions")))
                .collect(Collectors.toList());

        return ResponseEntity.ok(academyStats);
    }
}
