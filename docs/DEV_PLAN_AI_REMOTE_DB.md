# 개발서버 AI 고도화 개발 플랜

> **목적**: 개발서버에서 AI 모델 고도화를 진행하면서, 데이터 수집/집계는 운영 MacBook DB를 직접 참조하는 환경 구성
>
> **작성일**: 2026-02-11

---

## 1. 아키텍처 개요

### 현재 구조 (단일 서버)

```
┌────────────────── MacBook (study.unmong.com) ──────────────────┐
│                                                                 │
│  [PostgreSQL :5432]                                             │
│       ▲                                                         │
│       ├── [ai-crawler] 크롤링 + 집계 + AI 분석                  │
│       ├── [backend]    Spring Boot API (:9010)                  │
│       └── [frontend]   React (:4010)                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 목표 구조 (역할 분리)

```
┌─── MacBook (운영) ────────┐          ┌─── 개발서버 ──────────────┐
│                            │          │                            │
│  [PostgreSQL :5432]  ◄──── SSH ─────  │  [ai-crawler]              │
│       ▲                    │  Tunnel  │   --mode ai-only           │
│       │                    │ (:15432) │                            │
│  [ai-crawler]              │          │  AI 고도화 작업:            │
│   - 크롤링 (01:00)         │          │  - 감성분석 모델 개선       │
│   - 리포트 (01:30)         │          │  - Ollama LLM 통합         │
│   - 주간집계 (월 02:00)    │          │  - 새 크롤러 개발           │
│                            │          │  - 분석 파이프라인 실험      │
│  [backend + frontend]      │          │                            │
│                            │          │  [Ollama :11434]           │
└────────────────────────────┘          └────────────────────────────┘
```

### 역할 분담 정리

| 구분 | MacBook (운영) | 개발서버 |
|------|----------------|----------|
| PostgreSQL | 운영 (유일한 DB) | 미설치 (원격 접속) |
| 크롤링 스케줄러 | 가동 (매일 01:00) | 비활성화 |
| 리포트/집계 | 가동 (01:30, 월 02:00) | 비활성화 |
| AI 분석 실험 | - | 주 작업 영역 |
| Ollama | 선택사항 | 주 실행 환경 |
| backend/frontend | 운영 | - |

---

## 2. 환경 구성

### 2-1. SSH 터널 설정

개발서버에서 운영 MacBook DB에 접속하기 위한 SSH 터널을 구성한다.

```bash
# 개발서버에서 실행
# 로컬 15432 포트 → MacBook의 PostgreSQL 5432 포트
ssh -L 15432:localhost:5432 <user>@study.unmong.com -N -f

# 연결 확인
psql -h localhost -p 15432 -U postgres -d teacherhub -c "SELECT count(*) FROM posts;"
```

**자동 재연결 (systemd 또는 autossh 사용 권장)**:

```bash
# autossh로 끊김 자동 복구
autossh -M 0 -f -N -L 15432:localhost:5432 <user>@study.unmong.com \
  -o "ServerAliveInterval=30" \
  -o "ServerAliveCountMax=3"
```

### 2-2. 환경변수 파일

개발서버 전용 `.env.dev-remote` 파일을 생성한다.

```env
# .env.dev-remote
# 개발서버에서 운영 DB 접속용 환경변수

# Database (SSH 터널 경유)
DB_HOST=host.docker.internal   # Docker 컨테이너 → 호스트
DB_PORT=15432                  # SSH 터널 포트
DB_USER=postgres
DB_PASS=postgres123
DB_NAME=teacherhub

# AI 서비스
OLLAMA_HOST=http://host.docker.internal:11434

# 실행 모드
APP_MODE=ai-only               # 크롤링/스케줄러 비활성화
```

> `.env.dev-remote` 파일은 반드시 `.gitignore`에 추가할 것

### 2-3. Docker Compose Override 파일

`docker-compose.dev-remote.yml`을 생성하여 개발서버 환경을 구성한다.

```yaml
# docker-compose.dev-remote.yml
# 개발서버 전용: 운영 DB 원격 접속 + AI 작업 전용 모드
services:
  ai-crawler:
    build:
      context: ./ai-crawler
      dockerfile: Dockerfile
    container_name: teacherhub-ai-dev
    environment:
      TZ: Asia/Seoul
      DB_HOST: host.docker.internal
      DB_PORT: 15432
      DB_USER: postgres
      DB_PASS: postgres123
      DB_NAME: teacherhub
      OLLAMA_HOST: http://host.docker.internal:11434
      APP_MODE: ai-only
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./ai-crawler:/app               # 소스코드 마운트 (핫 리로드)
      - ./ai-crawler/data:/app/data
    networks:
      - dev-network
    restart: "no"                        # 개발 중이므로 자동 재시작 안 함
    command: python src/main.py --mode ai-only

networks:
  dev-network:
    driver: bridge
```

### 2-4. 개발서버 실행 방법

```bash
# 1. SSH 터널 시작
autossh -M 0 -f -N -L 15432:localhost:5432 <user>@study.unmong.com

# 2. 컨테이너 실행 (AI 전용 모드)
docker compose -f docker-compose.dev-remote.yml up --build

# 또는 Docker 없이 로컬 실행
export $(cat .env.dev-remote | xargs)
cd ai-crawler && python src/main.py --mode ai-only
```

---

## 3. 코드 변경사항

### 3-1. main.py에 실행 모드 분기 추가

`ai-crawler/src/main.py`에 `--mode` 인자를 추가하여 AI 전용 모드를 지원한다.

```python
# main.py 수정 방향

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['full', 'ai-only'], default='full')
    args = parser.parse_args()

    # DB 연결 대기
    if not wait_for_db():
        return
    init_db()

    if args.mode == 'full':
        # 기존 방식: 스케줄러 + Flask API + 크롤링 전체 실행
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        asyncio.run(run_scheduler_loop())

    elif args.mode == 'ai-only':
        # AI 전용 모드: Flask API만 실행 (실험/테스트용)
        # 스케줄러, 자동 크롤링 비활성화
        print("[*] AI-Only Mode: 스케줄러 비활성화, API만 실행")
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
```

### 3-2. CLI에 AI 실험용 커맨드 추가 (선택)

`ai-crawler/src/cli.py`에 AI 모델 테스트/실험용 커맨드를 추가할 수 있다.

```python
# cli.py에 추가할 커맨드 예시

@cli.command()
@click.option('--teacher-id', '-t', type=int, help='테스트할 강사 ID')
@click.option('--limit', '-l', default=100, help='분석할 멘션 수')
def ai_test(teacher_id, limit):
    """AI 분석 모델 테스트 (운영 데이터 기반)"""
    # 운영 DB에서 기존 멘션 데이터를 읽어서
    # 새로운 AI 모델로 분석 결과를 비교
    pass

@cli.command()
@click.option('--model', '-m', default='mistral', help='Ollama 모델명')
def ollama_test(model):
    """Ollama LLM 통합 테스트"""
    pass
```

---

## 4. DB 접근 정책

### 4-1. 테이블별 접근 권한

개발서버에서 운영 DB 접근 시, 테이블별로 읽기/쓰기 정책을 명확히 한다.

#### 읽기 전용 (SELECT만 허용)

운영 크롤링/집계 파이프라인이 관리하는 테이블이므로 개발서버에서 절대 수정하지 않는다.

| 테이블 | 설명 | 사유 |
|--------|------|------|
| `posts` | 수집된 게시글 | 운영 크롤러가 관리 |
| `comments` | 게시글 댓글 | 운영 크롤러가 관리 |
| `crawl_logs` | 크롤링 실행 로그 | 운영 스케줄러가 관리 |
| `collection_sources` | 수집 소스 설정 | 운영 설정 |
| `academies` | 학원 마스터 데이터 | 운영 설정 |
| `teachers` | 강사 마스터 데이터 | 운영 설정 |
| `subjects` | 과목 마스터 데이터 | 운영 설정 |
| `daily_reports` | 일일 리포트 | 운영 집계가 관리 |
| `weekly_reports` | 주간 리포트 | 운영 집계가 관리 |
| `academy_daily_stats` | 학원 일일 통계 | 운영 집계가 관리 |
| `academy_weekly_stats` | 학원 주간 통계 | 운영 집계가 관리 |
| `aggregation_logs` | 집계 로그 | 운영 집계가 관리 |

#### 읽기+쓰기 허용

AI 고도화 실험 결과를 저장하는 테이블은 개발서버에서도 쓰기가 가능하다.

| 테이블 | 설명 | 사유 |
|--------|------|------|
| `teacher_mentions` | 강사 멘션 (감성분석 결과) | AI 분석 결과 업데이트 대상 |
| `analysis_keywords` | 분석 키워드 사전 | AI 모델 개선 시 키워드 추가/수정 |
| `system_configs` | 시스템 설정 | 분석 설정값 조정 |

#### AI 실험 전용 테이블 (신규 생성 권장)

운영 데이터와 실험 데이터를 분리하기 위해 별도 테이블을 사용한다.

| 테이블 (신규) | 설명 |
|----------------|------|
| `ai_experiment_results` | AI 모델별 분석 결과 비교 |
| `ai_model_evaluations` | 모델 성능 평가 기록 |
| `ai_sentiment_v2` | 새 감성분석 결과 (기존 대비 비교용) |

```sql
-- 실험 결과 비교 테이블 예시
CREATE TABLE ai_experiment_results (
    id BIGSERIAL PRIMARY KEY,
    mention_id BIGINT REFERENCES teacher_mentions(id),
    model_name VARCHAR(100) NOT NULL,       -- 'keyword_v1', 'ollama_mistral', 'ollama_gemma' 등
    sentiment VARCHAR(20),
    sentiment_score DOUBLE PRECISION,
    difficulty VARCHAR(20),
    is_recommended BOOLEAN,
    raw_response TEXT,                       -- LLM 원본 응답
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 모델 성능 평가 테이블
CREATE TABLE ai_model_evaluations (
    id BIGSERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    evaluation_date DATE NOT NULL,
    total_samples INTEGER,
    accuracy DOUBLE PRECISION,
    precision_score DOUBLE PRECISION,
    recall_score DOUBLE PRECISION,
    f1_score DOUBLE PRECISION,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4-2. ddl-auto 설정

개발서버에서 운영 DB에 접속할 때는 **기존 테이블 스키마를 변경하지 않도록** 주의한다.

```python
# database.py 에서 init_db() 호출 시 주의
# APP_MODE=ai-only 일 때는 기존 테이블 create_all만 수행 (ALTER 없음)
# 신규 실험 테이블만 create_if_not_exists
```

> **주의**: `Base.metadata.create_all()`은 테이블이 없을 때만 생성하므로 기존 테이블에는 영향이 없지만, 모델 정의가 변경된 경우 예상치 못한 동작이 발생할 수 있다. 개발서버에서는 운영 모델 정의를 수정하지 않는다.

---

## 5. AI 고도화 작업 영역

### 5-1. 감성분석 모델 개선

**현재 상태**: 키워드 기반 규칙 분석 (`sentiment_analyzer.py`)

```
현재: "추천" → +weight → POSITIVE (단순 키워드 매칭)
목표: 문맥 기반 감성분석 (Ollama LLM 또는 한국어 NLP 모델)
```

**작업 내용**:

| 단계 | 작업 | 상세 |
|------|------|------|
| 1 | 기존 결과 벤치마크 | `teacher_mentions`에서 기존 감성분석 결과 추출, 정확도 기준선 수립 |
| 2 | Ollama 모델 테스트 | mistral, gemma 등 모델로 동일 텍스트 분석, 결과를 `ai_experiment_results`에 저장 |
| 3 | 프롬프트 엔지니어링 | 한국어 공무원 커뮤니티 맥락에 맞는 프롬프트 최적화 |
| 4 | 성능 비교 | 키워드 방식 vs LLM 방식 정확도/속도/비용 비교 |
| 5 | 하이브리드 적용 | 키워드 + LLM 조합 또는 LLM 단독으로 전환 |

**참조 데이터 (운영 DB에서 읽기)**:
- `teacher_mentions` → 기존 분석 결과 (sentiment, sentiment_score)
- `posts`, `comments` → 원문 텍스트
- `analysis_keywords` → 현재 키워드 사전

**결과 저장 (운영 DB에 쓰기)**:
- `ai_experiment_results` → 모델별 분석 결과 비교
- `ai_model_evaluations` → 모델 성능 평가

### 5-2. Ollama LLM 통합

**현재 상태**: OLLAMA_HOST 환경변수만 설정되어 있고, 실제 코드 통합은 미구현

**작업 내용**:

```
ai-crawler/src/services/
├── sentiment_analyzer.py      ← 기존 (키워드 기반)
├── llm_analyzer.py            ← 신규 (Ollama 기반)
└── analysis_pipeline.py       ← 신규 (분석 파이프라인 통합)
```

| 단계 | 작업 | 상세 |
|------|------|------|
| 1 | LLM 서비스 클래스 작성 | Ollama API 호출, 응답 파싱, 에러 처리 |
| 2 | 프롬프트 템플릿 설계 | 감성분석, 난이도 판단, 요약 생성 프롬프트 |
| 3 | 배치 처리 구현 | 대량 멘션을 효율적으로 LLM 분석하는 파이프라인 |
| 4 | 기존 분석기와 통합 | SentimentAnalyzer와 LLMAnalyzer를 전환 가능하게 구성 |
| 5 | 리포트 요약 개선 | `daily_reports.summary`를 LLM으로 생성 |

### 5-3. 신규 크롤러 개발/테스트

**현재 상태**: DCInside, Naver Cafe 크롤러 운영 중

**작업 내용**:

| 단계 | 작업 | 상세 |
|------|------|------|
| 1 | 새 크롤러 코드 작성 | `crawlers/` 디렉토리에 새 크롤러 추가 (예: 에펨코리아, 블라인드 등) |
| 2 | 로컬 테스트 | 개발서버에서 크롤러 단독 실행, 결과를 파일로 출력하여 검증 |
| 3 | DB 연동 테스트 | 운영 DB의 `collection_sources`에 새 소스 추가 후 통합 테스트 |
| 4 | 운영 배포 | 검증 완료 후 MacBook의 ai-crawler에 반영 |

> **주의**: 새 크롤러 테스트 시 `posts`, `comments` 테이블에 직접 쓰기 하지 않도록 한다. 테스트 데이터는 로컬 파일 또는 별도 테스트 테이블에 저장한다.

### 5-4. 분석 파이프라인 고도화

**현재 파이프라인**:

```
크롤링 → 멘션 추출 → 키워드 감성분석 → 일일 리포트 → 주간 집계
```

**목표 파이프라인**:

```
크롤링 → 멘션 추출 → [LLM 감성분석 + 키워드 보조]
                     → [LLM 요약 생성]
                     → [트렌드 이상탐지]
                     → 일일 리포트 → 주간 집계
```

---

## 6. 데이터 흐름 및 동시성 관리

### 6-1. 시간대별 작업 분리

운영 크롤링/집계와 개발서버 AI 작업이 DB에서 충돌하지 않도록 시간대를 분리한다.

```
시간(KST)  MacBook (운영)              개발서버 (AI)
─────────────────────────────────────────────────────
00:00      -                           AI 실험 가능
01:00      ■ 크롤링 시작                (DB 부하 증가, 대량 읽기 자제)
01:30      ■ 리포트 생성                (DB 부하 증가, 대량 읽기 자제)
02:00(월)  ■ 주간 집계                  (DB 부하 증가, 대량 읽기 자제)
03:00      -                           AI 실험 가능
 ...       -                           AI 실험 가능
09:00~     backend API 서빙             AI 실험 가능 (적절한 부하 유지)
```

### 6-2. 동시 쓰기 방지 규칙

| 상황 | 규칙 |
|------|------|
| `teacher_mentions` 기존 레코드 수정 | 개발서버에서 직접 UPDATE 금지. `ai_experiment_results`에 별도 저장 |
| `teacher_mentions` 감성분석 결과 반영 | 검증 완료 후 일괄 UPDATE 스크립트로 반영 (운영 크롤링 시간 외) |
| `analysis_keywords` 키워드 추가 | 즉시 반영 가능 (운영 분석에도 적용됨을 인지) |
| 신규 테이블 생성 | `ai_` 접두사 사용, 개발서버에서 자유롭게 생성 |

---

## 7. 개발 워크플로우

### 7-1. 일상적인 개발 흐름

```
1. SSH 터널 확인 (autossh 상태 확인)
       ↓
2. 개발서버에서 ai-crawler 실행 (--mode ai-only)
       ↓
3. 운영 DB에서 데이터 조회 (posts, mentions 등)
       ↓
4. 새 AI 모델로 분석 실험
       ↓
5. 결과를 ai_experiment_results에 저장
       ↓
6. 기존 키워드 방식과 비교 평가
       ↓
7. 코드 커밋 (git push)
       ↓
8. 검증 완료 시 운영 MacBook에 배포
```

### 7-2. 운영 반영 절차

AI 모델 고도화 결과를 운영에 반영할 때의 절차:

```
1. 개발서버에서 충분한 테스트 완료
       ↓
2. ai_experiment_results vs teacher_mentions 성능 비교 리포트 작성
       ↓
3. MacBook에서 git pull로 코드 반영
       ↓
4. docker compose -f docker-compose.prod.yml up --build -d
       ↓
5. 운영 모니터링 (crawl_logs, daily_reports 정상 생성 확인)
```

---

## 8. 주요 파일 참조

### 운영 이해에 필요한 핵심 파일

| 파일 | 역할 | 비고 |
|------|------|------|
| `ai-crawler/src/database.py` | DB 연결 설정 | 환경변수로 접속 정보 제어 |
| `ai-crawler/src/models.py` | 전체 테이블 정의 (15개) | 운영 스키마 변경 금지 |
| `ai-crawler/src/main.py` | 메인 진입점 | `--mode ai-only` 분기 추가 대상 |
| `ai-crawler/src/scheduler.py` | 크롤링/집계 스케줄러 | 개발서버에서 비활성화 |
| `ai-crawler/src/orchestrator.py` | 크롤링 오케스트레이션 | 크롤러 매핑 및 파이프라인 |
| `ai-crawler/src/services/sentiment_analyzer.py` | 감성분석 (키워드) | 고도화 대상 |
| `ai-crawler/src/services/teacher_matcher.py` | 강사명 매칭 | 정규식 기반 |
| `ai-crawler/src/services/mention_extractor.py` | 멘션 추출 + 분석 | AI 파이프라인 통합 지점 |
| `ai-crawler/src/services/report_generator.py` | 일일 리포트 생성 | 요약 생성 고도화 대상 |
| `ai-crawler/src/services/weekly_aggregator.py` | 주간 집계 | 트렌드 분석 고도화 가능 |

### Backend API (참고용)

| 엔드포인트 | 용도 |
|-------------|------|
| `GET /api/v2/reports/daily?date=` | 일일 리포트 조회 |
| `GET /api/v2/reports/weekly?year=&week=` | 주간 리포트 조회 |
| `GET /api/v2/weekly/teacher/{id}/trend` | 강사 트렌드 |
| `GET /api/v2/teachers/search?q=` | 강사 검색 |

---

## 9. 체크리스트

### 환경 구성 시

- [ ] SSH 키 기반 인증 설정 (MacBook ↔ 개발서버)
- [ ] autossh 설치 및 터널 자동 시작 설정
- [ ] `.env.dev-remote` 파일 생성
- [ ] `.gitignore`에 `.env.dev-remote` 추가
- [ ] `docker-compose.dev-remote.yml` 생성
- [ ] DB 연결 테스트 (`SELECT count(*) FROM posts`)
- [ ] `ai_experiment_results` 테이블 생성
- [ ] `ai_model_evaluations` 테이블 생성

### AI 고도화 작업 시

- [ ] 운영 테이블 직접 수정 금지 확인
- [ ] `ai_` 접두사 테이블에만 실험 결과 저장
- [ ] 크롤링 시간대 (01:00~02:30) 대량 쿼리 자제
- [ ] 새 모델 적용 전 기존 방식과 성능 비교 완료
- [ ] `--mode ai-only`로 스케줄러 비활성화 상태 확인

### 운영 반영 시

- [ ] 개발서버에서 충분한 테스트 완료
- [ ] 성능 비교 리포트 작성
- [ ] MacBook에서 `git pull` + `docker compose up --build`
- [ ] 운영 정상 동작 확인 (crawl_logs, daily_reports)
