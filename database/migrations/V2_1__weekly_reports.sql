-- ============================================
-- TeacherHub V2.1 - Weekly Reports Schema
-- 주간 리포트 및 집계 테이블
-- ============================================

-- 주간 리포트 테이블
CREATE TABLE IF NOT EXISTS weekly_reports (
    id BIGSERIAL PRIMARY KEY,
    teacher_id BIGINT NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    academy_id BIGINT NOT NULL REFERENCES academies(id) ON DELETE CASCADE,

    -- 기간 정보
    year INT NOT NULL,
    week_number INT NOT NULL,              -- ISO week number (1-53)
    week_start_date DATE NOT NULL,         -- 월요일
    week_end_date DATE NOT NULL,           -- 일요일

    -- 언급 통계
    mention_count INT DEFAULT 0,
    positive_count INT DEFAULT 0,
    negative_count INT DEFAULT 0,
    neutral_count INT DEFAULT 0,
    recommendation_count INT DEFAULT 0,

    -- 난이도 통계
    difficulty_easy_count INT DEFAULT 0,
    difficulty_medium_count INT DEFAULT 0,
    difficulty_hard_count INT DEFAULT 0,

    -- 계산 지표
    avg_sentiment_score DECIMAL(5,4),
    sentiment_trend DECIMAL(5,4),          -- 전주 대비 감성 변화
    mention_change_rate DECIMAL(6,2),      -- 전주 대비 언급 변화율 (%)
    weekly_rank INT,                        -- 해당 주 전체 순위
    academy_rank INT,                       -- 학원 내 순위

    -- 분석 데이터 (JSON)
    top_keywords JSONB DEFAULT '[]',
    source_distribution JSONB DEFAULT '{}', -- 출처별 분포 {"naver_cafe": 10, "dcinside": 5}
    daily_distribution JSONB DEFAULT '{}',  -- 요일별 분포
    mention_types JSONB DEFAULT '{}',       -- 멘션 타입별 분포

    -- AI 요약
    ai_summary TEXT,
    highlight_positive TEXT,               -- 대표 긍정 멘션
    highlight_negative TEXT,               -- 대표 부정 멘션

    -- 메타데이터
    is_complete BOOLEAN DEFAULT FALSE,     -- 주간 완료 여부
    aggregated_at TIMESTAMP,               -- 집계 시간
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 복합 유니크 제약
    CONSTRAINT uk_weekly_teacher_year_week UNIQUE (teacher_id, year, week_number)
);

-- 학원별 주간 통계 테이블
CREATE TABLE IF NOT EXISTS academy_weekly_stats (
    id BIGSERIAL PRIMARY KEY,
    academy_id BIGINT NOT NULL REFERENCES academies(id) ON DELETE CASCADE,

    -- 기간 정보
    year INT NOT NULL,
    week_number INT NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,

    -- 통계
    total_mentions INT DEFAULT 0,
    total_teachers_mentioned INT DEFAULT 0,
    avg_sentiment_score DECIMAL(5,4),
    total_positive INT DEFAULT 0,
    total_negative INT DEFAULT 0,
    total_recommendations INT DEFAULT 0,

    -- 랭킹 정보
    top_teacher_id BIGINT REFERENCES teachers(id),
    top_teacher_mentions INT DEFAULT 0,

    -- 분석 데이터
    top_keywords JSONB DEFAULT '[]',
    source_distribution JSONB DEFAULT '{}',

    -- 메타데이터
    aggregated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_academy_weekly_year_week UNIQUE (academy_id, year, week_number)
);

-- 집계 작업 로그 테이블
CREATE TABLE IF NOT EXISTS aggregation_logs (
    id BIGSERIAL PRIMARY KEY,
    aggregation_type VARCHAR(50) NOT NULL,  -- 'daily', 'weekly', 'monthly'
    target_date DATE,
    year INT,
    week_number INT,

    -- 상태
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- 결과
    records_processed INT DEFAULT 0,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 시스템 설정 테이블 (환경별 설정 관리)
CREATE TABLE IF NOT EXISTS system_configs (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string',  -- string, int, boolean, json
    description TEXT,
    environment VARCHAR(20) DEFAULT 'all',     -- all, dev, prod
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_weekly_reports_teacher ON weekly_reports(teacher_id);
CREATE INDEX IF NOT EXISTS idx_weekly_reports_academy ON weekly_reports(academy_id);
CREATE INDEX IF NOT EXISTS idx_weekly_reports_year_week ON weekly_reports(year, week_number);
CREATE INDEX IF NOT EXISTS idx_weekly_reports_dates ON weekly_reports(week_start_date, week_end_date);
CREATE INDEX IF NOT EXISTS idx_academy_weekly_academy ON academy_weekly_stats(academy_id);
CREATE INDEX IF NOT EXISTS idx_academy_weekly_year_week ON academy_weekly_stats(year, week_number);
CREATE INDEX IF NOT EXISTS idx_aggregation_logs_type_date ON aggregation_logs(aggregation_type, target_date);

-- 주간 리포트 조회 뷰 (하이브리드 방식 지원)
CREATE OR REPLACE VIEW v_teacher_weekly_summary AS
SELECT
    wr.id,
    wr.teacher_id,
    t.name as teacher_name,
    wr.academy_id,
    a.name as academy_name,
    s.name as subject_name,
    wr.year,
    wr.week_number,
    wr.week_start_date,
    wr.week_end_date,
    wr.mention_count,
    wr.positive_count,
    wr.negative_count,
    wr.neutral_count,
    wr.recommendation_count,
    wr.avg_sentiment_score,
    wr.mention_change_rate,
    wr.weekly_rank,
    wr.academy_rank,
    wr.top_keywords,
    wr.ai_summary,
    wr.is_complete
FROM weekly_reports wr
JOIN teachers t ON wr.teacher_id = t.id
JOIN academies a ON wr.academy_id = a.id
LEFT JOIN subjects s ON t.subject_id = s.id
WHERE t.is_active = TRUE;

-- 현재 주 실시간 집계 함수
CREATE OR REPLACE FUNCTION get_current_week_stats(p_teacher_id BIGINT)
RETURNS TABLE (
    mention_count BIGINT,
    positive_count BIGINT,
    negative_count BIGINT,
    neutral_count BIGINT,
    recommendation_count BIGINT,
    avg_sentiment_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(SUM(dr.mention_count), 0)::BIGINT,
        COALESCE(SUM(dr.positive_count), 0)::BIGINT,
        COALESCE(SUM(dr.negative_count), 0)::BIGINT,
        COALESCE(SUM(dr.neutral_count), 0)::BIGINT,
        COALESCE(SUM(dr.recommendation_count), 0)::BIGINT,
        COALESCE(AVG(dr.avg_sentiment_score), 0)::DECIMAL
    FROM daily_reports dr
    WHERE dr.teacher_id = p_teacher_id
    AND dr.report_date >= date_trunc('week', CURRENT_DATE)::DATE
    AND dr.report_date <= CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- 초기 시스템 설정 삽입
INSERT INTO system_configs (config_key, config_value, config_type, description, environment) VALUES
('weekly_aggregation_day', '1', 'int', '주간 집계 실행 요일 (1=월요일)', 'all'),
('weekly_aggregation_hour', '2', 'int', '주간 집계 실행 시간 (24시간)', 'all'),
('crawler_interval_hours', '6', 'int', '크롤러 실행 간격 (시간)', 'prod'),
('crawler_interval_hours', '24', 'int', '크롤러 실행 간격 (시간)', 'dev'),
('max_mentions_per_crawl', '100', 'int', '크롤링 당 최대 멘션 수', 'all'),
('sentiment_threshold_positive', '0.2', 'string', '긍정 판단 임계값', 'all'),
('sentiment_threshold_negative', '-0.2', 'string', '부정 판단 임계값', 'all')
ON CONFLICT (config_key) DO NOTHING;
