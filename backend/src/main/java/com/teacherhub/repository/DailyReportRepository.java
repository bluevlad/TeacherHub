package com.teacherhub.repository;

import com.teacherhub.domain.DailyReport;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface DailyReportRepository extends JpaRepository<DailyReport, Long> {

    Optional<DailyReport> findByReportDateAndTeacherId(LocalDate reportDate, Long teacherId);

    List<DailyReport> findByReportDate(LocalDate reportDate);

    List<DailyReport> findByTeacherIdOrderByReportDateDesc(Long teacherId);

    @Query("SELECT dr FROM DailyReport dr WHERE dr.teacher.id = :teacherId " +
           "AND dr.reportDate >= :startDate ORDER BY dr.reportDate DESC")
    List<DailyReport> findTeacherHistory(
        @Param("teacherId") Long teacherId,
        @Param("startDate") LocalDate startDate
    );

    @Query("SELECT dr FROM DailyReport dr WHERE dr.reportDate = :reportDate " +
           "ORDER BY dr.mentionCount DESC")
    List<DailyReport> findTopMentionedByDate(@Param("reportDate") LocalDate reportDate);

    @Query("SELECT dr FROM DailyReport dr JOIN dr.teacher t " +
           "WHERE t.academy.id = :academyId AND dr.reportDate = :reportDate " +
           "ORDER BY dr.mentionCount DESC")
    List<DailyReport> findByAcademyAndDate(
        @Param("academyId") Long academyId,
        @Param("reportDate") LocalDate reportDate
    );
}
