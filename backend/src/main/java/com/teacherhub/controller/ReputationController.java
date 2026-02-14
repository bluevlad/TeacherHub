package com.teacherhub.controller;

import com.teacherhub.dto.KeywordStats;
import com.teacherhub.dto.MonthlyStats;
import com.teacherhub.domain.ReputationData;
import com.teacherhub.repository.ReputationRepository;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/reputation")
@RequiredArgsConstructor
@Validated
public class ReputationController {

    private final ReputationRepository reputationRepository;

    @GetMapping
    public List<ReputationData> getAll() {
        return reputationRepository.findAllByOrderByCreatedAtDesc();
    }

    @GetMapping("/stats")
    public Map<String, Object> getStats(
            @RequestParam @NotBlank @Size(max = 100, message = "키워드는 100자 이내입니다") String keyword) {
        Map<String, Object> result = new HashMap<>();

        // 1. Total Posts
        long totalPosts = reputationRepository.countByKeyword(keyword);

        // 2. Total Comments (handle null)
        Long totalComments = reputationRepository.countTotalCommentsByKeyword(keyword);
        if (totalComments == null)
            totalComments = 0L;

        // 3. Last Year Monthly Stats
        LocalDateTime oneYearAgo = LocalDateTime.now().minusYears(1);
        List<MonthlyStats> monthlyStats = reputationRepository.findMonthlyStats(keyword, oneYearAgo);

        result.put("keyword", keyword);
        result.put("totalPosts", totalPosts);
        result.put("totalComments", totalComments);
        result.put("monthlyStats", monthlyStats);

        return result;
    }
}
