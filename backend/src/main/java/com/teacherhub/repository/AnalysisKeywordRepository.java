package com.teacherhub.repository;

import com.teacherhub.domain.AnalysisKeyword;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface AnalysisKeywordRepository extends JpaRepository<AnalysisKeyword, Long> {

    List<AnalysisKeyword> findByCategory(String category);

    List<AnalysisKeyword> findByCategoryAndIsActiveTrue(String category);

    List<AnalysisKeyword> findByIsActiveTrue();

    Optional<AnalysisKeyword> findByCategoryAndKeyword(String category, String keyword);
}
