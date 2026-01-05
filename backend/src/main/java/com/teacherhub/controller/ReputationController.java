package com.teacherhub.controller;

import com.teacherhub.domain.ReputationData;
import com.teacherhub.repository.ReputationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/reputation")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // Allow all for demo
public class ReputationController {

    private final ReputationRepository reputationRepository;

    @GetMapping
    public List<ReputationData> getAll() {
        return reputationRepository.findAllByOrderByCreatedAtDesc();
    }
}
