# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 상위 `C:/GIT/CLAUDE.md`의 Git-First Workflow를 상속합니다.

## Project Overview

TeacherHub - 공무원 학원 강사 평판 분석 시스템 (디시인사이드/네이버카페 크롤링 → AI 감성 분석 → 대시보드/랭킹)

## Environment

- **Database**: PostgreSQL 15 (Oracle/H2 문법 사용 금지)
- **Target Server**: MacBook Docker (172.30.1.72) / Windows 로컬 개발
- **Docker Strategy**: DB-only Docker 로컬 (`docker-compose.local.yml`) / 전체 서비스 운영 (`docker-compose.prod.yml`)
- **Java Version**: 17
- **Spring Boot Version**: 3.2.0

## Tech Stack

### Backend (backend/)

| 항목 | 기술 |
|------|------|
| Language | Java 17 |
| Framework | Spring Boot 3.2.0 |
| ORM | Spring Data JPA |
| Database | PostgreSQL 15 |
| Build Tool | Gradle |
| Utility | Lombok |

### Frontend (frontend/)

| 항목 | 기술 |
|------|------|
| Language | JavaScript |
| Framework | React 18 (CRA) |
| UI Library | Material-UI 5 |
| Chart | Chart.js 4 + react-chartjs-2 |
| HTTP Client | Axios |

### AI Crawler (ai-crawler/)

| 항목 | 기술 |
|------|------|
| Language | Python |
| AI | Ollama (로컬 LLM), TextBlob (감성 분석) |
| Crawler | Playwright (브라우저 자동화), BeautifulSoup4 |
| Scheduler | APScheduler |
| DB 연결 | SQLAlchemy + psycopg2 (PostgreSQL 직접) |
| Data | pandas |

## Build and Run Commands

```bash
# Backend
cd backend
./gradlew build
./gradlew bootRun
./gradlew test

# Frontend
cd frontend
npm install
npm start           # 개발 서버 (CRA)
npm run build       # 프로덕션 빌드
npm test            # 테스트

# 로컬 DB (PostgreSQL only)
docker compose -f docker-compose.local.yml up -d

# 운영 전체 서비스
docker compose -f docker-compose.prod.yml up -d

# E2E 테스트 (e2e/)
cd e2e
npm install
npx playwright install
npm run test        # Playwright 테스트
npm run test:ui     # UI 모드
```

### Port Mapping

| 서비스 | 로컬 | Docker (운영) |
|--------|------|---------------|
| Backend API | 8081 | 9010:8080 |
| Frontend | 3000 | 4010:4010 |
| PostgreSQL | 5432 | 5432:5432 |
| AI Crawler | - | (내부) |

## Architecture Overview

```
com.teacherhub/
├── controller/     # REST Controller
├── domain/         # Entity
├── dto/            # Data Transfer Objects
├── repository/     # JPA Repository
├── service/        # Business Logic
└── TeacherHubApplication.java
```

### 3-Tier Architecture
- Backend: Controller → Service → Repository (JPA)
- AI Crawler: Python → PostgreSQL 직접 → Ollama 분석
- Frontend: React → Axios → Backend API

## Do NOT

- Oracle 문법 사용 금지 (예: NVL → COALESCE, SYSDATE → CURRENT_TIMESTAMP)
- H2 호환성 가정 금지 — PostgreSQL 전용 기능 사용 가능
- 운영 Docker 컨테이너 직접 조작 금지 (teacherhub-backend, teacherhub-frontend, teacherhub-ai)
- 서버 주소, 비밀번호, 컨테이너명 추측 금지 — 반드시 확인 후 사용
- .env, credentials 파일 커밋 금지
- 자격증명(비밀번호, API 키)을 소스코드에 하드코딩하지 마라
- CORS에 allow_origins=["*"] 또는 origins="*" 사용하지 마라
- API 엔드포인트를 인증 없이 노출하지 마라
- console.log/print로 민감 정보를 출력하지 마라

## Database Notes

- SQL 문법: PostgreSQL 호환만 사용
- 페이지네이션: `LIMIT/OFFSET` 사용 (ROWNUM 금지)
- 날짜 함수: `CURRENT_TIMESTAMP`, `NOW()` 사용
- DDL 전략: `spring.jpa.hibernate.ddl-auto=validate` (운영)
- 마이그레이션: `database/migrations/` (Flyway 패턴)
- 초기화: `database/init.sql`, `v2_schema.sql`, `v2_seed_data.sql`

## Deployment

- **CI/CD**: GitHub Actions (prod 브랜치 push 시 자동 배포)
- **운영 포트**: Frontend 4010, Backend 9010 (외부) / 8080 (내부)
- **네트워크**: teacherhub-network (내부), database-network (외부 공유)

> 로컬 환경 정보는 `CLAUDE.local.md` 참조 (git에 포함되지 않음)
