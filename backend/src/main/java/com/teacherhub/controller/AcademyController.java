package com.teacherhub.controller;

import com.teacherhub.dto.AcademyDTO;
import com.teacherhub.dto.TeacherDTO;
import com.teacherhub.repository.AcademyRepository;
import com.teacherhub.service.TeacherService;
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
public class AcademyController {

    private final AcademyRepository academyRepository;
    private final TeacherService teacherService;

    @GetMapping
    public ResponseEntity<List<AcademyDTO>> getAllAcademies() {
        return ResponseEntity.ok(
                academyRepository.findByIsActiveTrue().stream()
                        .map(AcademyDTO::fromEntity)
                        .collect(Collectors.toList())
        );
    }

    @GetMapping("/{id}")
    public ResponseEntity<AcademyDTO> getAcademyById(@PathVariable Long id) {
        return academyRepository.findById(id)
                .map(AcademyDTO::fromEntity)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/{id}/teachers")
    public ResponseEntity<List<TeacherDTO>> getAcademyTeachers(@PathVariable Long id) {
        return ResponseEntity.ok(teacherService.getTeachersByAcademy(id));
    }
}
