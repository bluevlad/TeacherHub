-- ============================================
-- TeacherHub V2 Schema
-- 강사 평판 분석 시스템
-- 생성일: 2025-02-03
-- ============================================

-- 기존 테이블 유지 (reputation_data)
-- 새 테이블들은 기존 시스템과 병행 운영

-- ============================================
-- 1. 학원 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS academies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    website VARCHAR(200),
    logo_url VARCHAR(300),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE academies IS '공무원 학원 정보';
COMMENT ON COLUMN academies.code IS '학원 코드 (gongdangi, hackers, willbes, eduwill)';

-- ============================================
-- 2. 과목 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,  -- common, major, psat
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE subjects IS '시험 과목 정보';
COMMENT ON COLUMN subjects.category IS 'common(공통과목), major(전문과목), psat(PSAT)';

-- ============================================
-- 3. 강사 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    academy_id INTEGER REFERENCES academies(id) ON DELETE SET NULL,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    aliases TEXT[],  -- 별명, 이름 변형 배열
    profile_url VARCHAR(300),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE teachers IS '강사 정보';
COMMENT ON COLUMN teachers.aliases IS '강사 별명 배열 (검색용)';

CREATE INDEX IF NOT EXISTS idx_teachers_academy ON teachers(academy_id);
CREATE INDEX IF NOT EXISTS idx_teachers_subject ON teachers(subject_id);
CREATE INDEX IF NOT EXISTS idx_teachers_name ON teachers(name);

-- ============================================
-- 4. 수집 소스 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS collection_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,  -- naver_cafe, dcinside, fmkorea
    base_url VARCHAR(300),
    source_type VARCHAR(50),  -- cafe, gallery, forum
    is_active BOOLEAN DEFAULT TRUE,
    config JSONB,  -- 크롤링 설정 (로그인 필요 여부 등)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE collection_sources IS '데이터 수집 소스 정보';

-- ============================================
-- 5. 게시글 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES collection_sources(id),
    external_id VARCHAR(100),  -- 원본 게시글 ID
    title VARCHAR(500) NOT NULL,
    content TEXT,
    url VARCHAR(500),
    author VARCHAR(100),
    post_date TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(source_id, external_id)
);

COMMENT ON TABLE posts IS '수집된 게시글';

CREATE INDEX IF NOT EXISTS idx_posts_source ON posts(source_id);
CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(post_date);
CREATE INDEX IF NOT EXISTS idx_posts_collected ON posts(collected_at);

-- ============================================
-- 6. 댓글 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    external_id VARCHAR(100),
    content TEXT,
    author VARCHAR(100),
    comment_date TIMESTAMP,
    like_count INTEGER DEFAULT 0,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE comments IS '게시글 댓글';

CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);

-- ============================================
-- 7. 강사 멘션 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS teacher_mentions (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,

    mention_type VARCHAR(20) NOT NULL,  -- title, content, comment
    matched_text VARCHAR(200),  -- 매칭된 텍스트
    context TEXT,  -- 주변 문맥 (앞뒤 100자)

    -- 분석 결과
    sentiment VARCHAR(20),  -- POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score DOUBLE PRECISION,  -- -1.0 ~ 1.0
    difficulty VARCHAR(20),  -- EASY, MEDIUM, HARD
    is_recommended BOOLEAN,

    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(teacher_id, post_id, comment_id, mention_type)
);

COMMENT ON TABLE teacher_mentions IS '강사 멘션 및 분석 결과';
COMMENT ON COLUMN teacher_mentions.mention_type IS 'title(제목), content(본문), comment(댓글)';
COMMENT ON COLUMN teacher_mentions.sentiment IS 'POSITIVE(긍정), NEGATIVE(부정), NEUTRAL(중립)';
COMMENT ON COLUMN teacher_mentions.difficulty IS 'EASY(쉬움), MEDIUM(보통), HARD(어려움)';

CREATE INDEX IF NOT EXISTS idx_mentions_teacher ON teacher_mentions(teacher_id);
CREATE INDEX IF NOT EXISTS idx_mentions_post ON teacher_mentions(post_id);
CREATE INDEX IF NOT EXISTS idx_mentions_analyzed ON teacher_mentions(analyzed_at);

-- ============================================
-- 8. 데일리 리포트 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS daily_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE CASCADE,

    -- 집계 데이터
    mention_count INTEGER DEFAULT 0,
    post_mention_count INTEGER DEFAULT 0,
    comment_mention_count INTEGER DEFAULT 0,

    -- 감성 분석 집계
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    avg_sentiment_score DOUBLE PRECISION,

    -- 난이도 집계
    difficulty_easy_count INTEGER DEFAULT 0,
    difficulty_medium_count INTEGER DEFAULT 0,
    difficulty_hard_count INTEGER DEFAULT 0,

    -- 추천 집계
    recommendation_count INTEGER DEFAULT 0,

    -- 전일 대비 변화
    mention_change INTEGER DEFAULT 0,  -- 전일 대비 증감
    sentiment_change DOUBLE PRECISION,  -- 전일 대비 감성 변화

    -- AI 요약
    summary TEXT,
    top_keywords TEXT[],  -- 자주 언급된 키워드

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(report_date, teacher_id)
);

COMMENT ON TABLE daily_reports IS '강사별 데일리 리포트';

CREATE INDEX IF NOT EXISTS idx_reports_date ON daily_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_reports_teacher ON daily_reports(teacher_id);

-- ============================================
-- 9. 학원별 데일리 집계 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS academy_daily_stats (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    academy_id INTEGER REFERENCES academies(id) ON DELETE CASCADE,

    total_mentions INTEGER DEFAULT 0,
    total_teachers_mentioned INTEGER DEFAULT 0,
    avg_sentiment_score DOUBLE PRECISION,
    top_teacher_id INTEGER REFERENCES teachers(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(report_date, academy_id)
);

COMMENT ON TABLE academy_daily_stats IS '학원별 데일리 통계';

-- ============================================
-- 10. 크롤링 작업 로그 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS crawl_logs (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES collection_sources(id),
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- running, completed, failed
    posts_collected INTEGER DEFAULT 0,
    comments_collected INTEGER DEFAULT 0,
    mentions_found INTEGER DEFAULT 0,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE crawl_logs IS '크롤링 작업 로그';

-- ============================================
-- 11. 분석 키워드 사전 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS analysis_keywords (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,  -- sentiment_positive, sentiment_negative, difficulty_easy, difficulty_hard, recommendation
    keyword VARCHAR(100) NOT NULL,
    weight DOUBLE PRECISION DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE,

    UNIQUE(category, keyword)
);

COMMENT ON TABLE analysis_keywords IS '분석용 키워드 사전';

-- 기본 키워드 삽입
INSERT INTO analysis_keywords (category, keyword, weight) VALUES
-- 긍정 키워드
('sentiment_positive', '추천', 1.5),
('sentiment_positive', '강추', 2.0),
('sentiment_positive', '좋아요', 1.0),
('sentiment_positive', '감사', 1.0),
('sentiment_positive', '합격', 1.5),
('sentiment_positive', '최고', 1.5),
('sentiment_positive', '도움', 1.0),
('sentiment_positive', '굿', 1.0),
('sentiment_positive', '명강의', 2.0),
('sentiment_positive', '이해', 1.0),
('sentiment_positive', '쉽게', 1.0),
('sentiment_positive', '친절', 1.0),
('sentiment_positive', '꼼꼼', 1.0),
('sentiment_positive', '체계적', 1.5),
('sentiment_positive', '효율적', 1.0),
-- 부정 키워드
('sentiment_negative', '비추', 2.0),
('sentiment_negative', '별로', 1.0),
('sentiment_negative', '어렵', 1.0),
('sentiment_negative', '실망', 1.5),
('sentiment_negative', '환불', 2.0),
('sentiment_negative', '답답', 1.0),
('sentiment_negative', '부족', 1.0),
('sentiment_negative', '아쉽', 0.8),
('sentiment_negative', '불친절', 1.5),
('sentiment_negative', '졸림', 1.0),
('sentiment_negative', '지루', 1.0),
('sentiment_negative', '돈아까', 2.0),
-- 난이도 쉬움
('difficulty_easy', '쉬움', 1.0),
('difficulty_easy', '쉽게', 1.0),
('difficulty_easy', '기초', 0.8),
('difficulty_easy', '입문', 0.8),
('difficulty_easy', '초보', 0.8),
('difficulty_easy', '친절', 0.5),
('difficulty_easy', '이해됨', 1.0),
-- 난이도 어려움
('difficulty_hard', '어려움', 1.0),
('difficulty_hard', '어렵', 1.0),
('difficulty_hard', '심화', 0.8),
('difficulty_hard', '고급', 0.8),
('difficulty_hard', '빡셈', 1.5),
('difficulty_hard', '헬', 1.5),
('difficulty_hard', '멘붕', 1.0),
-- 추천
('recommendation', '추천', 1.0),
('recommendation', '강추', 1.5),
('recommendation', '들어라', 1.0),
('recommendation', '꼭', 0.5),
('recommendation', '필수', 1.0),
('recommendation', '인생강의', 2.0)
ON CONFLICT (category, keyword) DO NOTHING;

-- ============================================
-- 뷰: 강사별 최신 통계
-- ============================================
CREATE OR REPLACE VIEW v_teacher_latest_stats AS
SELECT
    t.id AS teacher_id,
    t.name AS teacher_name,
    a.name AS academy_name,
    s.name AS subject_name,
    dr.report_date,
    dr.mention_count,
    dr.positive_count,
    dr.negative_count,
    dr.neutral_count,
    dr.avg_sentiment_score,
    dr.recommendation_count,
    dr.mention_change
FROM teachers t
LEFT JOIN academies a ON t.academy_id = a.id
LEFT JOIN subjects s ON t.subject_id = s.id
LEFT JOIN daily_reports dr ON t.id = dr.teacher_id
WHERE dr.report_date = (SELECT MAX(report_date) FROM daily_reports WHERE teacher_id = t.id)
ORDER BY dr.mention_count DESC NULLS LAST;

-- ============================================
-- 뷰: 학원별 강사 랭킹
-- ============================================
CREATE OR REPLACE VIEW v_academy_teacher_ranking AS
SELECT
    a.id AS academy_id,
    a.name AS academy_name,
    t.id AS teacher_id,
    t.name AS teacher_name,
    s.name AS subject_name,
    COALESCE(SUM(dr.mention_count), 0) AS total_mentions,
    COALESCE(AVG(dr.avg_sentiment_score), 0) AS avg_sentiment,
    RANK() OVER (PARTITION BY a.id ORDER BY SUM(dr.mention_count) DESC NULLS LAST) AS mention_rank
FROM academies a
JOIN teachers t ON a.id = t.academy_id
LEFT JOIN subjects s ON t.subject_id = s.id
LEFT JOIN daily_reports dr ON t.id = dr.teacher_id
WHERE dr.report_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.id, a.name, t.id, t.name, s.name
ORDER BY a.name, mention_rank;
