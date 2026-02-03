package com.teacherhub.repository;

import com.teacherhub.domain.Post;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface PostRepository extends JpaRepository<Post, Long> {

    Optional<Post> findBySourceIdAndExternalId(Long sourceId, String externalId);

    List<Post> findBySourceId(Long sourceId);

    List<Post> findByPostDateBetween(LocalDateTime start, LocalDateTime end);

    @Query("SELECT p FROM Post p WHERE p.source.id = :sourceId AND p.postDate BETWEEN :start AND :end ORDER BY p.postDate DESC")
    List<Post> findBySourceAndDateRange(
        @Param("sourceId") Long sourceId,
        @Param("start") LocalDateTime start,
        @Param("end") LocalDateTime end
    );

    @Query("SELECT COUNT(p) FROM Post p WHERE p.source.id = :sourceId AND p.collectedAt >= :since")
    Long countRecentBySource(@Param("sourceId") Long sourceId, @Param("since") LocalDateTime since);
}
