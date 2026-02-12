package com.teacherhub.service;

import com.teacherhub.domain.Teacher;
import com.teacherhub.dto.TeacherDTO;
import com.teacherhub.repository.TeacherRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class TeacherService {

    private final TeacherRepository teacherRepository;

    public List<TeacherDTO> getAllTeachers(Long academyId) {
        List<Teacher> teachers;
        if (academyId != null) {
            teachers = teacherRepository.findByAcademyIdAndIsActiveTrue(academyId);
        } else {
            teachers = teacherRepository.findByIsActiveTrue();
        }
        return teachers.stream().map(TeacherDTO::fromEntity).collect(Collectors.toList());
    }

    public Optional<TeacherDTO> getTeacherById(Long id) {
        return teacherRepository.findById(id).map(TeacherDTO::fromEntity);
    }

    public List<TeacherDTO> searchTeachers(String searchTerm) {
        if (searchTerm == null || searchTerm.isBlank() || searchTerm.length() > 100) {
            return List.of();
        }
        String sanitized = searchTerm.strip();

        // JPQL name search + native alias search, merge & deduplicate
        Set<Long> seenIds = new HashSet<>();
        List<TeacherDTO> results = new ArrayList<>();

        for (Teacher t : teacherRepository.searchByName(sanitized)) {
            if (seenIds.add(t.getId())) {
                results.add(TeacherDTO.fromEntity(t));
            }
        }
        for (Teacher t : teacherRepository.searchByAlias(sanitized)) {
            if (seenIds.add(t.getId())) {
                results.add(TeacherDTO.fromEntity(t));
            }
        }
        return results;
    }

    public List<TeacherDTO> getTeachersByAcademy(Long academyId) {
        return teacherRepository.findByAcademyIdAndIsActiveTrue(academyId)
                .stream().map(TeacherDTO::fromEntity).collect(Collectors.toList());
    }
}
