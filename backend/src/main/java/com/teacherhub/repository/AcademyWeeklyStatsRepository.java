package com.teacherhub.repository;

import com.teacherhub.domain.AcademyWeeklyStats;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 학원별 주간 통계 Repository
 */
@Repository
public interface AcademyWeeklyStatsRepository extends JpaRepository<AcademyWeeklyStats, Long> {

    /**
     * 특정 학원의 주간 통계 조회
     */
    Optional<AcademyWeeklyStats> findByAcademyIdAndYearAndWeekNumber(
        Long academyId, Integer year, Integer weekNumber);

    /**
     * 특정 주차의 모든 학원 통계 조회
     */
    List<AcademyWeeklyStats> findByYearAndWeekNumberOrderByTotalMentionsDesc(
        Integer year, Integer weekNumber);

    /**
     * 학원의 최근 N주 통계 조회
     */
    @Query("SELECT aws FROM AcademyWeeklyStats aws " +
           "WHERE aws.academy.id = :academyId " +
           "ORDER BY aws.year DESC, aws.weekNumber DESC")
    List<AcademyWeeklyStats> findRecentByAcademyId(
        @Param("academyId") Long academyId,
        org.springframework.data.domain.Pageable pageable);

    /**
     * 학원 트렌드 데이터 조회
     */
    @Query("SELECT aws FROM AcademyWeeklyStats aws " +
           "WHERE aws.academy.id = :academyId " +
           "ORDER BY aws.year ASC, aws.weekNumber ASC")
    List<AcademyWeeklyStats> findTrendByAcademyId(@Param("academyId") Long academyId);
}
