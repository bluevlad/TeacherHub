package com.teacherhub.repository;

import com.teacherhub.domain.Academy;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface AcademyRepository extends JpaRepository<Academy, Long> {

    Optional<Academy> findByCode(String code);

    List<Academy> findByIsActiveTrue();

    List<Academy> findAllByOrderByNameAsc();
}
