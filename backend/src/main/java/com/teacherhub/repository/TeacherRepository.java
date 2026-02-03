package com.teacherhub.repository;

import com.teacherhub.domain.Teacher;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface TeacherRepository extends JpaRepository<Teacher, Long> {

    Optional<Teacher> findByName(String name);

    List<Teacher> findByAcademyId(Long academyId);

    List<Teacher> findByAcademyIdAndIsActiveTrue(Long academyId);

    List<Teacher> findBySubjectId(Long subjectId);

    List<Teacher> findByIsActiveTrue();

    @Query("SELECT t FROM Teacher t WHERE t.name LIKE %:searchTerm% OR :searchTerm = ANY(t.aliases)")
    List<Teacher> searchByNameOrAlias(@Param("searchTerm") String searchTerm);

    @Query("SELECT t FROM Teacher t JOIN t.academy a WHERE a.code = :academyCode AND t.isActive = true")
    List<Teacher> findByAcademyCode(@Param("academyCode") String academyCode);
}
