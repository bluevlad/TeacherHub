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

    // JOIN FETCH로 Teacher + Academy + Subject 일괄 로딩 (N+1 방지)
    @Query("SELECT dr FROM DailyReport dr " +
           "LEFT JOIN FETCH dr.teacher t " +
           "LEFT JOIN FETCH t.academy " +
           "LEFT JOIN FETCH t.subject " +
           "WHERE dr.reportDate = :reportDate")
    List<DailyReport> findByReportDateWithTeacher(@Param("reportDate") LocalDate reportDate);

    @Query("SELECT dr FROM DailyReport dr " +
           "LEFT JOIN FETCH dr.teacher t " +
           "LEFT JOIN FETCH t.academy " +
           "LEFT JOIN FETCH t.subject " +
           "WHERE t.id = :teacherId " +
           "AND dr.reportDate >= :startDate ORDER BY dr.reportDate DESC")
    List<DailyReport> findTeacherHistory(
        @Param("teacherId") Long teacherId,
        @Param("startDate") LocalDate startDate
    );

    @Query("SELECT dr FROM DailyReport dr " +
           "LEFT JOIN FETCH dr.teacher t " +
           "LEFT JOIN FETCH t.academy " +
           "LEFT JOIN FETCH t.subject " +
           "WHERE dr.reportDate = :reportDate " +
           "ORDER BY dr.mentionCount DESC")
    List<DailyReport> findTopMentionedByDate(@Param("reportDate") LocalDate reportDate);

    @Query("SELECT dr FROM DailyReport dr " +
           "LEFT JOIN FETCH dr.teacher t " +
           "LEFT JOIN FETCH t.academy a " +
           "LEFT JOIN FETCH t.subject " +
           "WHERE a.id = :academyId AND dr.reportDate = :reportDate " +
           "ORDER BY dr.mentionCount DESC")
    List<DailyReport> findByAcademyAndDate(
        @Param("academyId") Long academyId,
        @Param("reportDate") LocalDate reportDate
    );

    // 날짜 범위 조회 (주별/월별 리포트용)
    @Query("SELECT dr FROM DailyReport dr " +
           "LEFT JOIN FETCH dr.teacher t " +
           "LEFT JOIN FETCH t.academy " +
           "LEFT JOIN FETCH t.subject " +
           "WHERE dr.reportDate BETWEEN :startDate AND :endDate")
    List<DailyReport> findByReportDateBetweenWithTeacher(
        @Param("startDate") LocalDate startDate,
        @Param("endDate") LocalDate endDate
    );
}
