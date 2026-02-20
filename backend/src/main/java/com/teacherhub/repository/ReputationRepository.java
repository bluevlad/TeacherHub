package com.teacherhub.repository;

import com.teacherhub.domain.ReputationData;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface ReputationRepository extends JpaRepository<ReputationData, Long> {
    List<ReputationData> findAllByOrderByCreatedAtDesc();

    long countByKeyword(String keyword);

    @Query("SELECT SUM(r.commentCount) FROM ReputationData r WHERE r.keyword = :keyword")
    Long countTotalCommentsByKeyword(@Param("keyword") String keyword);

    /**
     * 키워드 및 시작일 이후의 ReputationData 조회
     * Java 코드에서 월별 그룹핑 수행 (PostgreSQL TO_CHAR 종속성 제거)
     */
    @Query("SELECT r FROM ReputationData r " +
            "WHERE r.keyword = :keyword AND r.postDate >= :startDate " +
            "ORDER BY r.postDate ASC")
    List<ReputationData> findByKeywordAndPostDateAfter(
            @Param("keyword") String keyword,
            @Param("startDate") LocalDateTime startDate);
}
