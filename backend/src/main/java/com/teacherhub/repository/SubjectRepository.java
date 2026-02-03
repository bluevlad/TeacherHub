package com.teacherhub.repository;

import com.teacherhub.domain.Subject;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SubjectRepository extends JpaRepository<Subject, Long> {

    Optional<Subject> findByName(String name);

    List<Subject> findByCategory(String category);

    List<Subject> findAllByOrderByDisplayOrderAsc();
}
