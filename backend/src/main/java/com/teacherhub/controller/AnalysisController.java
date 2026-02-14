package com.teacherhub.controller;

import com.teacherhub.dto.DailyReportDTO;
import com.teacherhub.service.AnalysisService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 감성 분석 결과 API Controller
 */
@RestController
@RequestMapping("/api/v2/analysis")
@RequiredArgsConstructor
@Validated
public class AnalysisController {

    private final AnalysisService analysisService;

    @GetMapping("/today")
    public ResponseEntity<List<DailyReportDTO>> getTodayReports() {
        return ResponseEntity.ok(analysisService.getReportsByDate(LocalDate.now()));
    }

    @GetMapping("/reports")
    public ResponseEntity<List<DailyReportDTO>> getReportsByDate(
            @RequestParam(required = false) String date) {
        LocalDate reportDate = date != null ? LocalDate.parse(date) : LocalDate.now();
        return ResponseEntity.ok(analysisService.getReportsByDate(reportDate));
    }

    @GetMapping("/teachers/{teacherId}/reports")
    public ResponseEntity<List<DailyReportDTO>> getTeacherReports(
            @PathVariable Long teacherId,
            @RequestParam(required = false) @Min(1) @Max(365) Integer days) {
        int daysBack = days != null ? days : 30;
        return ResponseEntity.ok(analysisService.getTeacherReports(teacherId, daysBack));
    }

    @GetMapping("/academies/{academyId}/reports")
    public ResponseEntity<List<DailyReportDTO>> getAcademyReports(
            @PathVariable Long academyId,
            @RequestParam(required = false) String date) {
        LocalDate reportDate = date != null ? LocalDate.parse(date) : LocalDate.now();
        return ResponseEntity.ok(analysisService.getAcademyReports(academyId, reportDate));
    }

    @GetMapping("/summary")
    public ResponseEntity<Map<String, Object>> getSummary() {
        return ResponseEntity.ok(analysisService.getSummary(LocalDate.now()));
    }

    @GetMapping("/ranking")
    public ResponseEntity<List<DailyReportDTO>> getRanking(
            @RequestParam(defaultValue = "mentions") String type,
            @RequestParam(defaultValue = "10") @Min(1) @Max(100) int limit) {
        List<DailyReportDTO> reports = analysisService.getReportsByDate(LocalDate.now());
        return ResponseEntity.ok(reports.stream().limit(limit).toList());
    }

    @GetMapping("/academy-stats")
    public ResponseEntity<List<Map<String, Object>>> getAcademyStats() {
        return ResponseEntity.ok(analysisService.getAcademyStats(LocalDate.now()));
    }
}
