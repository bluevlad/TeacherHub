package com.teacherhub.controller;

import com.teacherhub.domain.Academy;
import com.teacherhub.domain.Teacher;
import com.teacherhub.dto.AcademyDTO;
import com.teacherhub.dto.TeacherDTO;
import com.teacherhub.repository.AcademyRepository;
import com.teacherhub.repository.TeacherRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 학원 API Controller
 */
@RestController
@RequestMapping("/api/v2/academies")
@RequiredArgsConstructor
@CrossOrigin(origins = {"${app.cors.allowed-origins:http://localhost:3000}"})
public class AcademyController {

    private final AcademyRepository academyRepository;
    private final TeacherRepository teacherRepository;

    /**
     * 모든 학원 조회
     * GET /api/v2/academies
     */
    @GetMapping
    public ResponseEntity<List<AcademyDTO>> getAllAcademies() {
        List<Academy> academies = academyRepository.findByIsActiveTrue();
        List<AcademyDTO> dtos = academies.stream()
                .map(AcademyDTO::fromEntity)
                .collect(Collectors.toList());
        return ResponseEntity.ok(dtos);
    }

    /**
     * 학원 상세 조회
     * GET /api/v2/academies/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<AcademyDTO> getAcademyById(@PathVariable Long id) {
        return academyRepository.findById(id)
                .map(AcademyDTO::fromEntity)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * 학원 소속 강사 조회
     * GET /api/v2/academies/{id}/teachers
     */
    @GetMapping("/{id}/teachers")
    public ResponseEntity<List<TeacherDTO>> getAcademyTeachers(@PathVariable Long id) {
        List<Teacher> teachers = teacherRepository.findByAcademyIdAndIsActiveTrue(id);
        List<TeacherDTO> dtos = teachers.stream()
                .map(TeacherDTO::fromEntity)
                .collect(Collectors.toList());
        return ResponseEntity.ok(dtos);
    }
}
