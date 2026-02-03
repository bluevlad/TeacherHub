package com.teacherhub.repository;

import com.teacherhub.domain.TeacherMention;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface TeacherMentionRepository extends JpaRepository<TeacherMention, Long> {

    List<TeacherMention> findByTeacherId(Long teacherId);

    List<TeacherMention> findByPostId(Long postId);

    @Query("SELECT tm FROM TeacherMention tm JOIN tm.post p " +
           "WHERE tm.teacher.id = :teacherId AND p.postDate BETWEEN :start AND :end")
    List<TeacherMention> findByTeacherAndDateRange(
        @Param("teacherId") Long teacherId,
        @Param("start") LocalDateTime start,
        @Param("end") LocalDateTime end
    );

    @Query("SELECT tm.sentiment, COUNT(tm) FROM TeacherMention tm " +
           "WHERE tm.teacher.id = :teacherId GROUP BY tm.sentiment")
    List<Object[]> countBySentimentForTeacher(@Param("teacherId") Long teacherId);

    @Query("SELECT AVG(tm.sentimentScore) FROM TeacherMention tm " +
           "WHERE tm.teacher.id = :teacherId AND tm.sentimentScore IS NOT NULL")
    Double getAvgSentimentScore(@Param("teacherId") Long teacherId);

    @Query("SELECT COUNT(tm) FROM TeacherMention tm " +
           "WHERE tm.teacher.id = :teacherId AND tm.isRecommended = true")
    Long countRecommendations(@Param("teacherId") Long teacherId);
}
