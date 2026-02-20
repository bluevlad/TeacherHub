package com.teacherhub.controller;

import com.teacherhub.domain.ReputationData;
import com.teacherhub.dto.MonthlyStats;
import com.teacherhub.dto.ReputationDataDTO;
import com.teacherhub.repository.ReputationRepository;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/reputation")
@RequiredArgsConstructor
@Validated
public class ReputationController {

    private static final DateTimeFormatter YEAR_MONTH_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM");

    private final ReputationRepository reputationRepository;

    @GetMapping
    public List<ReputationDataDTO> getAll() {
        return reputationRepository.findAllByOrderByCreatedAtDesc().stream()
                .map(ReputationDataDTO::fromEntity)
                .collect(Collectors.toList());
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

        // 3. Last Year Monthly Stats (Java 그룹핑으로 PostgreSQL TO_CHAR 종속성 제거)
        LocalDateTime oneYearAgo = LocalDateTime.now().minusYears(1);
        List<ReputationData> reputationDataList = reputationRepository
                .findByKeywordAndPostDateAfter(keyword, oneYearAgo);

        // Java에서 월별 그룹핑 수행
        Map<String, Long> monthlyCountMap = reputationDataList.stream()
                .filter(r -> r.getPostDate() != null)
                .collect(Collectors.groupingBy(
                        r -> r.getPostDate().format(YEAR_MONTH_FORMAT),
                        TreeMap::new,
                        Collectors.counting()
                ));

        List<MonthlyStats> monthlyStats = monthlyCountMap.entrySet().stream()
                .map(entry -> new MonthlyStats(entry.getKey(), entry.getValue()))
                .collect(Collectors.toList());

        result.put("keyword", keyword);
        result.put("totalPosts", totalPosts);
        result.put("totalComments", totalComments);
        result.put("monthlyStats", monthlyStats);

        return result;
    }
}
