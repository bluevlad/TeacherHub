package com.teacherhub.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class KeywordStats {
    private String keyword;
    private long totalPosts;
    private long totalComments;
}
