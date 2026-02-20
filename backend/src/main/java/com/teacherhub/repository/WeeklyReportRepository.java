package com.teacherhub.repository;

import com.teacherhub.domain.WeeklyReport;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 주간 리포트 Repository
 */
@Repository
public interface WeeklyReportRepository extends JpaRepository<WeeklyReport, Long> {

    /**
     * 특정 강사의 주간 리포트 조회 (JOIN FETCH로 Teacher, Academy 일괄 로딩)
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "JOIN FETCH wr.teacher t " +
           "JOIN FETCH wr.academy a " +
           "WHERE t.id = :teacherId AND wr.year = :year AND wr.weekNumber = :weekNumber")
    Optional<WeeklyReport> findByTeacherIdAndYearAndWeekNumber(
        @Param("teacherId") Long teacherId,
        @Param("year") Integer year,
        @Param("weekNumber") Integer weekNumber);

    /**
     * 특정 주차의 모든 리포트 조회 (JOIN FETCH + 순위순)
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "JOIN FETCH wr.teacher t " +
           "JOIN FETCH wr.academy a " +
           "WHERE wr.year = :year AND wr.weekNumber = :weekNumber " +
           "ORDER BY wr.mentionCount DESC")
    List<WeeklyReport> findByYearAndWeekNumberOrderByMentionCountDesc(
        @Param("year") Integer year,
        @Param("weekNumber") Integer weekNumber);

    /**
     * 특정 학원의 주간 리포트 조회 (JOIN FETCH)
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "JOIN FETCH wr.teacher t " +
           "JOIN FETCH wr.academy a " +
           "WHERE a.id = :academyId AND wr.year = :year AND wr.weekNumber = :weekNumber " +
           "ORDER BY wr.mentionCount DESC")
    List<WeeklyReport> findByAcademyIdAndYearAndWeekNumberOrderByMentionCountDesc(
        @Param("academyId") Long academyId,
        @Param("year") Integer year,
        @Param("weekNumber") Integer weekNumber);

    /**
     * 강사의 최근 N주 리포트 조회 (JOIN FETCH)
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "JOIN FETCH wr.teacher t " +
           "JOIN FETCH wr.academy a " +
           "WHERE t.id = :teacherId " +
           "ORDER BY wr.year DESC, wr.weekNumber DESC")
    List<WeeklyReport> findRecentByTeacherId(
        @Param("teacherId") Long teacherId,
        org.springframework.data.domain.Pageable pageable);

    /**
     * 특정 주차 랭킹 조회 (JOIN FETCH + 상위 N명)
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "JOIN FETCH wr.teacher t " +
           "JOIN FETCH wr.academy a " +
           "WHERE wr.year = :year AND wr.weekNumber = :weekNumber " +
           "AND wr.mentionCount > 0 " +
           "ORDER BY wr.mentionCount DESC")
    List<WeeklyReport> findTopRankingByWeek(
        @Param("year") Integer year,
        @Param("weekNumber") Integer weekNumber,
        org.springframework.data.domain.Pageable pageable);

    /**
     * 학원별 주간 랭킹 조회 (JOIN FETCH)
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "JOIN FETCH wr.teacher t " +
           "JOIN FETCH wr.academy a " +
           "WHERE a.id = :academyId " +
           "AND wr.year = :year AND wr.weekNumber = :weekNumber " +
           "ORDER BY wr.mentionCount DESC")
    List<WeeklyReport> findByAcademyAndWeek(
        @Param("academyId") Long academyId,
        @Param("year") Integer year,
        @Param("weekNumber") Integer weekNumber);

    /**
     * 강사의 주간 트렌드 데이터 조회
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "WHERE wr.teacher.id = :teacherId " +
           "AND wr.isComplete = true " +
           "ORDER BY wr.year ASC, wr.weekNumber ASC")
    List<WeeklyReport> findTrendByTeacherId(@Param("teacherId") Long teacherId);

    /**
     * 완료된 주간 리포트 조회
     */
    List<WeeklyReport> findByYearAndWeekNumberAndIsCompleteTrue(
        Integer year, Integer weekNumber);

    /**
     * 학원의 복수 주차 리포트 일괄 조회 (N+1 방지 범위 쿼리)
     * getAcademyTrend에서 주차별 개별 쿼리 대신 사용
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "JOIN FETCH wr.teacher t " +
           "JOIN FETCH wr.academy a " +
           "WHERE a.id = :academyId " +
           "AND ((wr.year = :startYear AND wr.weekNumber >= :startWeek) " +
           "  OR (wr.year > :startYear AND wr.year < :endYear) " +
           "  OR (wr.year = :endYear AND wr.weekNumber <= :endWeek)) " +
           "ORDER BY wr.year ASC, wr.weekNumber ASC")
    List<WeeklyReport> findByAcademyAndWeekRange(
        @Param("academyId") Long academyId,
        @Param("startYear") Integer startYear,
        @Param("startWeek") Integer startWeek,
        @Param("endYear") Integer endYear,
        @Param("endWeek") Integer endWeek);
}
