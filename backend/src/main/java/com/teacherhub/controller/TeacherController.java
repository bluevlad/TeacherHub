package com.teacherhub.controller;

import com.teacherhub.dto.TeacherDTO;
import com.teacherhub.service.TeacherService;
import jakarta.validation.constraints.Size;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 강사 API Controller
 */
@RestController
@RequestMapping("/api/v2/teachers")
@RequiredArgsConstructor
@Validated
public class TeacherController {

    private final TeacherService teacherService;

    @GetMapping
    public ResponseEntity<List<TeacherDTO>> getAllTeachers(
            @RequestParam(required = false) Long academyId) {
        return ResponseEntity.ok(teacherService.getAllTeachers(academyId));
    }

    @GetMapping("/{id}")
    public ResponseEntity<TeacherDTO> getTeacherById(@PathVariable Long id) {
        return teacherService.getTeacherById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/search")
    public ResponseEntity<List<TeacherDTO>> searchTeachers(
            @RequestParam @Size(min = 1, max = 100, message = "검색어는 1~100자입니다") String q) {
        return ResponseEntity.ok(teacherService.searchTeachers(q));
    }
}
