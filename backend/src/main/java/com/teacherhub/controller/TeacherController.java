package com.teacherhub.controller;

import com.teacherhub.domain.Teacher;
import com.teacherhub.dto.TeacherDTO;
import com.teacherhub.repository.TeacherRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 강사 API Controller
 */
@RestController
@RequestMapping("/api/v2/teachers")
@RequiredArgsConstructor
@CrossOrigin(origins = {"${app.cors.allowed-origins:http://localhost:3000}"})
public class TeacherController {

    private final TeacherRepository teacherRepository;

    /**
     * 모든 강사 조회
     * GET /api/v2/teachers
     * GET /api/v2/teachers?academyId=1
     */
    @GetMapping
    public ResponseEntity<List<TeacherDTO>> getAllTeachers(
            @RequestParam(required = false) Long academyId) {
        List<Teacher> teachers;

        if (academyId != null) {
            teachers = teacherRepository.findByAcademyIdAndIsActiveTrue(academyId);
        } else {
            teachers = teacherRepository.findByIsActiveTrue();
        }

        List<TeacherDTO> dtos = teachers.stream()
                .map(TeacherDTO::fromEntity)
                .collect(Collectors.toList());

        return ResponseEntity.ok(dtos);
    }

    /**
     * 강사 상세 조회
     * GET /api/v2/teachers/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<TeacherDTO> getTeacherById(@PathVariable Long id) {
        return teacherRepository.findById(id)
                .map(TeacherDTO::fromEntity)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * 강사 검색
     * GET /api/v2/teachers/search?q=keyword
     */
    @GetMapping("/search")
    public ResponseEntity<List<TeacherDTO>> searchTeachers(@RequestParam String q) {
        List<Teacher> teachers = teacherRepository.searchByNameOrAlias(q);
        List<TeacherDTO> dtos = teachers.stream()
                .map(TeacherDTO::fromEntity)
                .collect(Collectors.toList());
        return ResponseEntity.ok(dtos);
    }
}
