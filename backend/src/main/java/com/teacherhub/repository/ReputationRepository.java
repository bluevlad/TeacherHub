package com.teacherhub.repository;

import com.teacherhub.domain.ReputationData;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ReputationRepository extends JpaRepository<ReputationData, Long> {
    List<ReputationData> findAllByOrderByCreatedAtDesc();
}
