# TeacherHub GitHub 리포지토리 구조 제안

**TeacherHub**와 같이 프론트엔드(React), 백엔드(Spring Boot), 그리고 데이터 수집/분석(Python)이 결합된 복합 프로젝트를 GitHub에서 효율적으로 관리하기 위한 구조를 제안합니다.

## 1. 리포지토리 전략: 모노레포 (Monorepo)

하나의 리포지토리 안에 모든 구성 요소를 담는 **모노레포** 방식을 추천합니다.
*   **장점**:
    *   프로젝트 전체의 이슈 및 일정 관리가 용이함 (GitHub Projects/Issues 통합 관리)
    *   배포 파이프라인(CI/CD)을 한 곳에서 설정 가능
    *   개발자 간의 코드 공유 및 협업이 직관적임
*   **단점**: 프로젝트 규모가 매우 커질 경우 CI 시간이 길어질 수 있음 (초기 단계에서는 문제 없음)

---

## 2. 디렉토리 구조 (Directory Structure)

루트 디렉토리 아래 성격이 다른 3개의 메인 프로젝트를 분리하여 구성합니다.

```
TeacherHub/
├── .github/                   # GitHub Actions (CI/CD) 및 템플릿
│   ├── workflows/             # 자동화 스크립트 (Build, Test, Deploy)
│   └── ISSUE_TEMPLATE/        # 이슈 작성 템플릿
├── ai-crawler/                # [Python] 데이터 수집 및 감성 분석 엔진
│   ├── src/
│   │   ├── collectors/        # 크롤러 모듈 (Naver, Daum, DC)
│   │   └── analysis/          # NLP 감성 분석 모델
│   ├── notebook/              # 데이터 분석 실험용 Jupyter Notebook
│   ├── tests/                 # 단위 테스트
│   ├── requirements.txt       # Python 의존성 목록
│   └── Dockerfile             # 크롤러 컨테이너 설정
├── backend/                   # [Spring Boot] API 서버
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/teacherhub/
│   │   │   └── resources/     # 설정 파일 (application.yml)
│   │   └── test/
│   ├── build.gradle           # 빌드 설정
│   └── Dockerfile             # API 서버 컨테이너 설정
├── frontend/                  # [React] 사용자 대시보드
│   ├── public/
│   ├── src/
│   │   ├── api/               # 백엔드 API 연동
│   │   ├── components/        # 공통 UI 컴포넌트
│   │   └── layouts/           # 페이지별 레이아웃
│   ├── package.json           # Node.js 의존성 목록
│   └── Dockerfile             # 웹 서버 컨테이너 설정
├── database/                  # [DB] 데이터베이스 관련 파일
│   ├── init/                  # 초기 데이터 및 테이블 생성 스크립트
│   └── docker-compose.yml     # 로컬 개발용 DB 실행 설정
├── docs/                      # 프로젝트 문서화
│   ├── architecture/          # 시스템 아키텍처 다이어그램
│   └── api/                   # API 명세서 (Swagger Export 등)
├── .gitignore                 # Git 제외 파일 설정
├── docker-compose.yml         # 전체 시스템 로컬 실행용 설정
└── README.md                  # 프로젝트 통합 설명서
```

---

## 3. 브랜치 전략 (Branching Strategy)

**Git Flow** 또는 **GitHub Flow**를 변형하여 사용합니다.

*   `main` (or `master`): 언제나 배포 가능한 안정 상태 (Production)
*   `develop`: 다음 버전을 위한 통합 브랜치 (Staging)
*   `feature/`: 새로운 기능 개발 브랜치
    *   작명 규칙: `feature/[prefix]-[기능명]`
    *   예시: `feature/fe-dashboard-chart` (프론트엔드), `feature/be-login-api` (백엔드), `feature/ai-crawler-naver` (크롤러)

---

## 4. 협업 및 이슈 관리 (Collaboration)

*   **Projects (Kanban)**: 'To Do', 'In Progress', 'Done'으로 작업 상태 시각화
*   **Issues**: 버그 제보, 기능 요청 등을 등록하고 담당자(Assignee) 및 라벨(Label) 지정
    *   Labels: `frontend`, `backend`, `ai`, `bug`, `enhancement`
*   **Pull Requests (PR)**: `develop` 브랜치로 병합 전 코드 리뷰 진행

---

## 5. CI/CD 자동화 (GitHub Actions)

각 폴더별로 변경 사항이 감지될 때만 워크플로우가 동작하도록 설정합니다.

*   `frontend/**` 변경 시: React 빌드 및 테스트 수행
*   `backend/**` 변경 시: Gradle 빌드 및 JUnit 테스트 수행
*   `ai-crawler/**` 변경 시: Lint 체크 및 단위 테스트 수행
