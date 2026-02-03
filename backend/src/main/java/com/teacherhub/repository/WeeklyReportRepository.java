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
     * 특정 강사의 주간 리포트 조회
     */
    Optional<WeeklyReport> findByTeacherIdAndYearAndWeekNumber(
        Long teacherId, Integer year, Integer weekNumber);

    /**
     * 특정 주차의 모든 리포트 조회 (순위순)
     */
    List<WeeklyReport> findByYearAndWeekNumberOrderByMentionCountDesc(
        Integer year, Integer weekNumber);

    /**
     * 특정 학원의 주간 리포트 조회
     */
    List<WeeklyReport> findByAcademyIdAndYearAndWeekNumberOrderByMentionCountDesc(
        Long academyId, Integer year, Integer weekNumber);

    /**
     * 강사의 최근 N주 리포트 조회
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "WHERE wr.teacher.id = :teacherId " +
           "ORDER BY wr.year DESC, wr.weekNumber DESC")
    List<WeeklyReport> findRecentByTeacherId(
        @Param("teacherId") Long teacherId,
        org.springframework.data.domain.Pageable pageable);

    /**
     * 특정 주차 랭킹 조회 (상위 N명)
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "WHERE wr.year = :year AND wr.weekNumber = :weekNumber " +
           "AND wr.mentionCount > 0 " +
           "ORDER BY wr.mentionCount DESC")
    List<WeeklyReport> findTopRankingByWeek(
        @Param("year") Integer year,
        @Param("weekNumber") Integer weekNumber,
        org.springframework.data.domain.Pageable pageable);

    /**
     * 학원별 주간 랭킹 조회
     */
    @Query("SELECT wr FROM WeeklyReport wr " +
           "WHERE wr.academy.id = :academyId " +
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
}
