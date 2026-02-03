package com.teacherhub.repository;

import com.teacherhub.domain.CollectionSource;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface CollectionSourceRepository extends JpaRepository<CollectionSource, Long> {

    Optional<CollectionSource> findByCode(String code);

    List<CollectionSource> findByIsActiveTrue();

    List<CollectionSource> findBySourceType(String sourceType);
}
