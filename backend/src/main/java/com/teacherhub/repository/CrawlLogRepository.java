package com.teacherhub.repository;

import com.teacherhub.domain.CrawlLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface CrawlLogRepository extends JpaRepository<CrawlLog, Long> {

    List<CrawlLog> findBySourceIdOrderByCreatedAtDesc(Long sourceId);

    List<CrawlLog> findByStatusOrderByCreatedAtDesc(String status);

    @Query("SELECT cl FROM CrawlLog cl ORDER BY cl.createdAt DESC")
    List<CrawlLog> findRecentLogs();

    @Query("SELECT cl FROM CrawlLog cl WHERE cl.source.id = :sourceId " +
           "ORDER BY cl.createdAt DESC LIMIT 1")
    Optional<CrawlLog> findLatestBySource(@Param("sourceId") Long sourceId);

    @Query("SELECT cl FROM CrawlLog cl WHERE cl.status = 'running' AND cl.startedAt < :threshold")
    List<CrawlLog> findStalledCrawls(@Param("threshold") LocalDateTime threshold);

    Long countBySourceIdAndStatus(Long sourceId, String status);
}
