package com.teacherhub.service;

import com.teacherhub.domain.DailyReport;
import com.teacherhub.dto.DailyReportDTO;
import com.teacherhub.repository.DailyReportRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AnalysisService {

    private final DailyReportRepository dailyReportRepository;

    public List<DailyReportDTO> getReportsByDate(LocalDate date) {
        List<DailyReport> reports = dailyReportRepository.findTopMentionedByDate(date);
        return reports.stream().map(DailyReportDTO::fromEntity).collect(Collectors.toList());
    }

    public List<DailyReportDTO> getTeacherReports(Long teacherId, int days) {
        LocalDate startDate = LocalDate.now().minusDays(days);
        List<DailyReport> reports = dailyReportRepository.findTeacherHistory(teacherId, startDate);
        return reports.stream().map(DailyReportDTO::fromEntity).collect(Collectors.toList());
    }

    public List<DailyReportDTO> getAcademyReports(Long academyId, LocalDate date) {
        List<DailyReport> reports = dailyReportRepository.findByAcademyAndDate(academyId, date);
        return reports.stream().map(DailyReportDTO::fromEntity).collect(Collectors.toList());
    }

    /**
     * 감성 분석 통계 집계 (공통 로직)
     */
    public Map<String, Object> aggregateSentimentStats(List<DailyReport> reports) {
        int totalMentions = reports.stream()
                .mapToInt(r -> r.getMentionCount() != null ? r.getMentionCount() : 0).sum();
        int totalPositive = reports.stream()
                .mapToInt(r -> r.getPositiveCount() != null ? r.getPositiveCount() : 0).sum();
        int totalNegative = reports.stream()
                .mapToInt(r -> r.getNegativeCount() != null ? r.getNegativeCount() : 0).sum();
        int totalNeutral = reports.stream()
                .mapToInt(r -> r.getNeutralCount() != null ? r.getNeutralCount() : 0).sum();

        double avgSentiment = reports.stream()
                .filter(r -> r.getAvgSentimentScore() != null)
                .mapToDouble(DailyReport::getAvgSentimentScore)
                .average().orElse(0.0);

        Map<String, Object> stats = new HashMap<>();
        stats.put("totalMentions", totalMentions);
        stats.put("totalPositive", totalPositive);
        stats.put("totalNegative", totalNegative);
        stats.put("totalNeutral", totalNeutral);
        stats.put("avgSentimentScore", Math.round(avgSentiment * 100.0) / 100.0);
        stats.put("positiveRatio", totalMentions > 0 ? Math.round(totalPositive * 100.0 / totalMentions) : 0);
        return stats;
    }

    public Map<String, Object> getSummary(LocalDate date) {
        List<DailyReport> reports = dailyReportRepository.findByReportDate(date);
        Map<String, Object> summary = aggregateSentimentStats(reports);
        summary.put("date", date);
        summary.put("totalTeachers", reports.size());
        return summary;
    }

    public List<Map<String, Object>> getAcademyStats(LocalDate date) {
        List<DailyReport> reports = dailyReportRepository.findByReportDate(date);

        Map<String, List<DailyReport>> byAcademy = reports.stream()
                .filter(r -> r.getTeacher() != null && r.getTeacher().getAcademy() != null)
                .collect(Collectors.groupingBy(r -> r.getTeacher().getAcademy().getName()));

        return byAcademy.entrySet().stream()
                .map(entry -> {
                    Map<String, Object> stat = aggregateSentimentStats(entry.getValue());
                    stat.put("academyName", entry.getKey());
                    stat.put("totalTeachersMentioned", entry.getValue().size());

                    DailyReport topTeacher = entry.getValue().stream()
                            .max((a, b) -> Integer.compare(
                                    a.getMentionCount() != null ? a.getMentionCount() : 0,
                                    b.getMentionCount() != null ? b.getMentionCount() : 0))
                            .orElse(null);
                    stat.put("topTeacherName", topTeacher != null && topTeacher.getTeacher() != null
                            ? topTeacher.getTeacher().getName() : null);
                    return stat;
                })
                .sorted((a, b) -> Integer.compare(
                        (Integer) b.get("totalMentions"), (Integer) a.get("totalMentions")))
                .collect(Collectors.toList());
    }
}
