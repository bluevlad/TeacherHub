package com.teacherhub.repository;

import com.teacherhub.domain.AcademyDailyStats;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface AcademyDailyStatsRepository extends JpaRepository<AcademyDailyStats, Long> {

    Optional<AcademyDailyStats> findByReportDateAndAcademyId(LocalDate reportDate, Long academyId);

    List<AcademyDailyStats> findByReportDate(LocalDate reportDate);

    List<AcademyDailyStats> findByAcademyIdOrderByReportDateDesc(Long academyId);

    @Query("SELECT ads FROM AcademyDailyStats ads WHERE ads.academy.id = :academyId " +
           "AND ads.reportDate >= :startDate ORDER BY ads.reportDate DESC")
    List<AcademyDailyStats> findAcademyHistory(
        @Param("academyId") Long academyId,
        @Param("startDate") LocalDate startDate
    );

    @Query("SELECT ads FROM AcademyDailyStats ads WHERE ads.reportDate = :reportDate " +
           "ORDER BY ads.totalMentions DESC")
    List<AcademyDailyStats> findTopAcademiesByDate(@Param("reportDate") LocalDate reportDate);
}
