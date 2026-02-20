package com.teacherhub.service;

import com.teacherhub.domain.WeeklyReport;
import com.teacherhub.dto.WeeklyReportDTO;
import com.teacherhub.dto.WeeklySummaryDTO;
import com.teacherhub.repository.WeeklyReportRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.temporal.IsoFields;
import java.time.temporal.TemporalAdjusters;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class WeeklyReportService {

    private final WeeklyReportRepository weeklyReportRepository;

    /**
     * 특정 주차의 모든 리포트 조회
     */
    public List<WeeklyReportDTO> getWeeklyReports(Integer year, Integer weekNumber) {
        Objects.requireNonNull(year, "year must not be null");
        Objects.requireNonNull(weekNumber, "weekNumber must not be null");

        List<WeeklyReport> reports = weeklyReportRepository
                .findByYearAndWeekNumberOrderByMentionCountDesc(year, weekNumber);
        return reports.stream()
                .map(WeeklyReportDTO::fromEntity)
                .collect(Collectors.toList());
    }

    /**
     * 특정 강사의 주간 리포트 조회
     */
    public Optional<WeeklyReportDTO> getTeacherWeeklyReport(Long teacherId, Integer year, Integer weekNumber) {
        Objects.requireNonNull(teacherId, "teacherId must not be null");
        Objects.requireNonNull(year, "year must not be null");
        Objects.requireNonNull(weekNumber, "weekNumber must not be null");

        return weeklyReportRepository
                .findByTeacherIdAndYearAndWeekNumber(teacherId, year, weekNumber)
                .map(WeeklyReportDTO::fromEntity);
    }

    /**
     * 주간 랭킹 조회
     */
    public List<WeeklyReportDTO> getWeeklyRanking(Integer year, Integer weekNumber, int limit) {
        Objects.requireNonNull(year, "year must not be null");
        Objects.requireNonNull(weekNumber, "weekNumber must not be null");

        List<WeeklyReport> reports = weeklyReportRepository
                .findTopRankingByWeek(year, weekNumber, PageRequest.of(0, limit));
        return reports.stream()
                .map(WeeklyReportDTO::fromEntity)
                .collect(Collectors.toList());
    }

    /**
     * 학원별 주간 리포트 조회
     */
    public List<WeeklyReportDTO> getAcademyWeeklyReports(Long academyId, Integer year, Integer weekNumber) {
        Objects.requireNonNull(academyId, "academyId must not be null");
        Objects.requireNonNull(year, "year must not be null");
        Objects.requireNonNull(weekNumber, "weekNumber must not be null");

        List<WeeklyReport> reports = weeklyReportRepository
                .findByAcademyAndWeek(academyId, year, weekNumber);
        return reports.stream()
                .map(WeeklyReportDTO::fromEntity)
                .collect(Collectors.toList());
    }

    /**
     * 강사 트렌드 조회 (최근 N주)
     */
    public List<WeeklyReportDTO> getTeacherTrend(Long teacherId, int weeks) {
        Objects.requireNonNull(teacherId, "teacherId must not be null");

        List<WeeklyReport> reports = weeklyReportRepository
                .findRecentByTeacherId(teacherId, PageRequest.of(0, weeks));
        // 시간순 정렬 (과거 -> 현재)
        Collections.reverse(reports);
        return reports.stream()
                .map(WeeklyReportDTO::fromEntity)
                .collect(Collectors.toList());
    }

    /**
     * 학원 트렌드 조회 (최근 N주)
     * 범위 쿼리 1회로 전체 데이터를 가져온 후 Java에서 주차별 그룹핑
     */
    public List<WeeklyReportDTO> getAcademyTrend(Long academyId, int weeks) {
        Objects.requireNonNull(academyId, "academyId must not be null");

        // 현재 주차 계산
        LocalDate now = LocalDate.now();
        int currentYear = now.get(IsoFields.WEEK_BASED_YEAR);
        int currentWeek = now.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR);

        // 시작 주차 계산
        int startYear = currentYear;
        int startWeek = currentWeek - (weeks - 1);
        while (startWeek <= 0) {
            startYear--;
            startWeek += 52;
        }

        // 범위 쿼리 1회로 전체 데이터 조회
        List<WeeklyReport> allReports = weeklyReportRepository
                .findByAcademyAndWeekRange(academyId, startYear, startWeek, currentYear, currentWeek);

        // 주차별 그룹핑 (year-week 키)
        Map<String, List<WeeklyReport>> groupedByWeek = allReports.stream()
                .collect(Collectors.groupingBy(
                        r -> r.getYear() + "-" + r.getWeekNumber(),
                        LinkedHashMap::new,
                        Collectors.toList()
                ));

        // 주차별 합산 데이터 생성
        List<WeeklyReportDTO> trendData = new ArrayList<>();
        for (Map.Entry<String, List<WeeklyReport>> entry : groupedByWeek.entrySet()) {
            List<WeeklyReport> weekReports = entry.getValue();
            if (!weekReports.isEmpty()) {
                int year = weekReports.get(0).getYear();
                int weekNumber = weekReports.get(0).getWeekNumber();
                trendData.add(aggregateAcademyReports(weekReports, year, weekNumber));
            }
        }

        return trendData;
    }

    /**
     * 현재 주차 정보 조회
     */
    public Map<String, Object> getCurrentWeekInfo() {
        LocalDate now = LocalDate.now();
        int year = now.get(IsoFields.WEEK_BASED_YEAR);
        int weekNumber = now.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR);

        LocalDate weekStart = now.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
        LocalDate weekEnd = weekStart.plusDays(6);

        Map<String, Object> result = new HashMap<>();
        result.put("year", year);
        result.put("week", weekNumber);
        result.put("weekLabel", year + "년 " + weekNumber + "주차");
        result.put("startDate", weekStart);
        result.put("endDate", weekEnd);
        return result;
    }

    /**
     * 주간 요약 통계 조회
     */
    public WeeklySummaryDTO getWeeklySummary(Integer year, Integer weekNumber) {
        Objects.requireNonNull(year, "year must not be null");
        Objects.requireNonNull(weekNumber, "weekNumber must not be null");

        List<WeeklyReport> reports = weeklyReportRepository
                .findByYearAndWeekNumberOrderByMentionCountDesc(year, weekNumber);

        if (reports.isEmpty()) {
            return WeeklySummaryDTO.builder()
                    .year(year)
                    .weekNumber(weekNumber)
                    .weekLabel(year + "년 " + weekNumber + "주차")
                    .totalMentions(0)
                    .totalPositive(0)
                    .totalNegative(0)
                    .totalRecommendations(0)
                    .totalTeachers(0)
                    .totalAcademies(0)
                    .build();
        }

        int totalMentions = reports.stream().mapToInt(WeeklyReport::getMentionCount).sum();
        int totalPositive = reports.stream().mapToInt(WeeklyReport::getPositiveCount).sum();
        int totalNegative = reports.stream().mapToInt(WeeklyReport::getNegativeCount).sum();
        int totalRecommendations = reports.stream().mapToInt(WeeklyReport::getRecommendationCount).sum();

        Set<Long> uniqueAcademies = reports.stream()
                .filter(r -> r.getAcademy() != null)
                .map(r -> r.getAcademy().getId())
                .collect(Collectors.toSet());

        BigDecimal avgSentiment = reports.stream()
                .filter(r -> r.getAvgSentimentScore() != null)
                .map(WeeklyReport::getAvgSentimentScore)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        long sentimentCount = reports.stream()
                .filter(r -> r.getAvgSentimentScore() != null)
                .count();

        if (sentimentCount > 0) {
            avgSentiment = avgSentiment.divide(BigDecimal.valueOf(sentimentCount), 4, RoundingMode.HALF_UP);
        }

        return WeeklySummaryDTO.builder()
                .year(year)
                .weekNumber(weekNumber)
                .weekLabel(year + "년 " + weekNumber + "주차")
                .totalMentions(totalMentions)
                .totalPositive(totalPositive)
                .totalNegative(totalNegative)
                .totalRecommendations(totalRecommendations)
                .totalTeachers(reports.size())
                .totalAcademies(uniqueAcademies.size())
                .avgSentimentScore(avgSentiment)
                .build();
    }

    /**
     * 학원 리포트 합산
     */
    private WeeklyReportDTO aggregateAcademyReports(List<WeeklyReport> reports, int year, int weekNumber) {
        int totalMentions = reports.stream().mapToInt(WeeklyReport::getMentionCount).sum();
        int totalPositive = reports.stream().mapToInt(WeeklyReport::getPositiveCount).sum();
        int totalNegative = reports.stream().mapToInt(WeeklyReport::getNegativeCount).sum();
        int totalNeutral = reports.stream().mapToInt(WeeklyReport::getNeutralCount).sum();
        int totalRecommendations = reports.stream().mapToInt(WeeklyReport::getRecommendationCount).sum();

        WeeklyReport first = reports.stream().findFirst().orElse(null);
        Long academyId = (first != null && first.getAcademy() != null) ? first.getAcademy().getId() : null;
        String academyName = (first != null && first.getAcademy() != null) ? first.getAcademy().getName() : "Unknown";

        return WeeklyReportDTO.builder()
                .academyId(academyId)
                .academyName(academyName)
                .year(year)
                .weekNumber(weekNumber)
                .weekLabel(year + "년 " + weekNumber + "주차")
                .mentionCount(totalMentions)
                .positiveCount(totalPositive)
                .negativeCount(totalNegative)
                .neutralCount(totalNeutral)
                .recommendationCount(totalRecommendations)
                .build();
    }
}
