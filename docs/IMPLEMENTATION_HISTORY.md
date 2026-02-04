# TeacherHub 구현 히스토리

## 프로젝트: 일별/주별/월별 데이터 조회 시스템

### 작업 시작일: 2026-02-04

---

## [Phase 1] 기본 구조 설계

### 1.1 요구사항 정의
- **목표**: 2026년 기준 일자별/주별/월별 감성 분석 데이터 조회
- **데이터 소스**: daily_reports 테이블 (일단위 크롤링 데이터)
- **집계 방식**: 실시간 쿼리 집계 (SUM, AVG)

### 1.2 주차 계산 기준
- ISO 8601 표준 (월요일 시작)
- 2026년 1월 예시:
  - 1주차: 2025-12-29(월) ~ 2026-01-04(일)
  - 2주차: 2026-01-05(월) ~ 2026-01-11(일)
  - ...

### 1.3 API 설계
```
GET /api/v2/reports/daily?date=2026-01-15
GET /api/v2/reports/weekly?year=2026&week=3
GET /api/v2/reports/monthly?year=2026&month=1
GET /api/v2/reports/periods - 선택 가능한 기간 목록
```

---

## [Phase 2] Backend 구현

### 2.1 ReportController 생성
- 파일: `backend/src/main/java/com/teacherhub/controller/ReportController.java`
- 시간: 2026-02-04 13:40

**구현 내용:**
- `GET /api/v2/reports/daily?date=` - 일별 리포트 조회
- `GET /api/v2/reports/weekly?year=&week=` - 주별 집계 리포트
- `GET /api/v2/reports/monthly?year=&month=` - 월별 집계 리포트
- `GET /api/v2/reports/periods` - 선택 가능한 기간 목록

**주요 로직:**
- 주차 계산: ISO 8601 (월요일 시작, WeekFields 사용)
- 집계 방식: daily_reports 테이블에서 기간별 SUM/AVG
- 강사별 그룹핑 후 전체 통계 산출

### 2.2 DTO 클래스 생성
- 파일: `backend/src/main/java/com/teacherhub/dto/PeriodReportDTO.java`
- 파일: `backend/src/main/java/com/teacherhub/dto/PeriodSummaryDTO.java`

**PeriodReportDTO 구조:**
```java
- periodType: daily/weekly/monthly
- startDate, endDate
- periodLabel: "2026년 2월 1주차"
- year, month, week
- totalTeachers, totalMentions
- totalPositive, totalNegative, totalNeutral
- avgSentimentScore, positiveRatio
- teacherSummaries: List<PeriodSummaryDTO>
```

**PeriodSummaryDTO 구조:**
```java
- teacherId, teacherName, academyName, subjectName
- mentionCount, positiveCount, negativeCount, neutralCount
- recommendationCount, avgSentimentScore
- reportDays
```

### 2.3 API 테스트 결과
- 시간: 2026-02-04 14:00

**일별 리포트 (/api/v2/reports/daily):**
```json
{
  "periodType": "daily",
  "totalTeachers": 12,
  "totalMentions": 134,
  "positiveRatio": 41%
}
```

**주별 리포트 (/api/v2/reports/weekly?year=2026&week=5):**
```json
{
  "periodType": "weekly",
  "periodLabel": "2026년 1월 5주차",
  "startDate": "2026-01-26",
  "endDate": "2026-02-01"
}
```

**기간 목록 (/api/v2/reports/periods):**
- daily: 최근 30일
- weekly: 2026년 1~6주차
- monthly: 2026년 1~2월

---

## [Phase 3] Frontend 구현

### 3.1 PeriodSelector 컴포넌트 생성
- 파일: `frontend/src/components/PeriodSelector.js`
- 시간: 2026-02-04 14:10

**기능:**
- 일별/주별/월별 탭 전환
- 각 기간 유형별 드롭다운 선택
- 선택 시 부모 컴포넌트에 콜백

**UI 구성:**
```
┌─────────────────────────────────────┐
│  [일별]  [주별]  [월별]              │  ← Tabs
├─────────────────────────────────────┤
│  [▼ 2월 4일 (수)                  ] │  ← Select
│                                     │
│  현재: [2월 4일 (수)]               │  ← Chip
└─────────────────────────────────────┘
```

### 3.2 Dashboard 컴포넌트 업데이트
- 파일: `frontend/src/pages/Dashboard.js`
- 시간: 2026-02-04 14:15

**변경 사항:**
- PeriodSelector 통합
- 기간 변경 시 API 호출 분기
- 통계 카드 동적 업데이트
- 강사 랭킹 테이블 개선 (긍정/부정 칩 추가)

### 3.3 API 클라이언트 업데이트
- 파일: `frontend/src/api/index.js`

**추가된 API:**
```javascript
reportApi = {
    getDaily: (date) => '/api/v2/reports/daily',
    getWeekly: (year, week) => '/api/v2/reports/weekly',
    getMonthly: (year, month) => '/api/v2/reports/monthly',
    getPeriods: () => '/api/v2/reports/periods'
}
```

---

## [Phase 4] 테스트 및 완료

### 4.1 통합 테스트
- 시간: 2026-02-04 14:20

**테스트 항목:**
- [x] Backend API 응답 확인
- [x] 일별 데이터 조회 정상
- [x] 주별 데이터 집계 정상
- [x] 기간 목록 조회 정상
- [x] Frontend 컴포넌트 렌더링
- [x] 기간 선택 시 데이터 변경

### 4.2 생성된 파일 목록

**Backend:**
1. `controller/ReportController.java` - 기간별 리포트 API
2. `dto/PeriodReportDTO.java` - 기간 리포트 DTO
3. `dto/PeriodSummaryDTO.java` - 강사별 집계 DTO

**Frontend:**
1. `components/PeriodSelector.js` - 기간 선택 컴포넌트
2. `pages/Dashboard.js` - 대시보드 (업데이트)
3. `api/index.js` - API 클라이언트 (업데이트)

**Documentation:**
1. `docs/IMPLEMENTATION_HISTORY.md` - 구현 히스토리

### 4.3 확인 방법
1. 브라우저에서 http://localhost:3000 접속
2. 일별/주별/월별 탭 전환
3. 드롭다운에서 기간 선택
4. 통계 카드 및 랭킹 테이블 확인

---

## 완료 요약

### 구현 완료 기능
1. **일별 조회**: 특정 날짜의 강사별 언급 통계
2. **주별 조회**: 주차별 집계 (ISO 8601 기준, 월요일 시작)
3. **월별 조회**: 월별 집계
4. **기간 선택 UI**: 탭 + 드롭다운 방식

### 데이터 흐름
```
daily_reports 테이블
    ↓
ReportController (집계)
    ↓
PeriodReportDTO / PeriodSummaryDTO
    ↓
Frontend API 호출
    ↓
PeriodSelector + Dashboard 렌더링
```

### 향후 개선 사항
1. 데이터 증가 시 weekly_reports 테이블 활용
2. 캐싱 적용 (Redis)
3. 트렌드 차트 추가
4. 기간 비교 기능

---

## [Phase 5] MacBook 배포 스크립트 구현

### 5.1 배포 스크립트 생성
- 시간: 2026-02-04 15:00

**생성된 스크립트:**

| 파일 | 실행 위치 | 설명 |
|------|----------|------|
| `deploy/build-and-export.sh` | Windows | Docker 이미지 빌드 및 tar 내보내기 |
| `deploy/import-and-run.sh` | MacBook | 이미지 가져오기 및 서비스 실행 |
| `deploy/backup-db.sh` | 양쪽 | PostgreSQL 데이터베이스 백업 |
| `deploy/restore-db.sh` | MacBook | PostgreSQL 데이터베이스 복원 |
| `deploy/MACBOOK_DEPLOY.md` | - | 배포 가이드 문서 |

### 5.2 OrbStack 환경 설정

**MacBook 서비스 포트:**
- Frontend: 4010 (내부 3000)
- Backend: 9010 (내부 8080)
- PostgreSQL: 내부 5432 (외부 노출 안함)

**이미지 네이밍 규칙:**
```
research-hub/teacherhub-api:latest
research-hub/teacherhub-front:latest
research-hub/teacherhub-ai:latest
```

### 5.3 배포 절차

```
[Windows]                              [MacBook]
    │                                      │
    ├─ build-and-export.sh ──────────────►│
    │   ├─ docker build                    │
    │   └─ docker save (tar)               │
    │                                      │
    ├─ backup-db.sh ─────────────────────►│
    │   └─ pg_dump                         │
    │                                      │
    ├─ scp *.tar *.sql.gz ───────────────►│
    │                                      │
    │                    import-and-run.sh ├
    │                        ├─ docker load│
    │                        └─ docker compose up
    │                                      │
    │                    restore-db.sh ────├
    │                        └─ psql restore
    │                                      │
    ▼                                      ▼
```

---

작업 완료: 2026-02-04 15:10

