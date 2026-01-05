package com.teacherhub.repository;

import com.teacherhub.domain.ReputationData;
import com.teacherhub.dto.MonthlyStats;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface ReputationRepository extends JpaRepository<ReputationData, Long> {
    List<ReputationData> findAllByOrderByCreatedAtDesc();

    long countByKeyword(String keyword);

    @Query("SELECT SUM(r.commentCount) FROM ReputationData r WHERE r.keyword = :keyword")
    Long countTotalCommentsByKeyword(String keyword);

    @Query("SELECT new com.teacherhub.dto.MonthlyStats(TO_CHAR(r.postDate, 'YYYY-MM'), COUNT(r)) " +
            "FROM ReputationData r " +
            "WHERE r.keyword = :keyword AND r.postDate >= :startDate " +
            "GROUP BY TO_CHAR(r.postDate, 'YYYY-MM') " +
            "ORDER BY TO_CHAR(r.postDate, 'YYYY-MM')")
    List<MonthlyStats> findMonthlyStats(String keyword, LocalDateTime startDate);
}
