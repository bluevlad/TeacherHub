# TeacherHub

**TeacherHub**는 학원 강사들이 자신(또는 특정 키워드)과 관련된 게시글을 주요 커뮤니티(네이버 카페, 다음 카페, 디시인사이드 등)에서 자동으로 수집하고, AI를 통해 긍정/부정 여부를 분석하여 통합 대시보드로 제공하는 평판 관리 시스템입니다.

## 🏗 시스템 아키텍처

이 프로젝트는 Docker 기반의 마이크로서비스 아키텍처로 구성되어 있습니다.

| 서비스 | 기술 스택 | 설명 |
|---|---|---|
| **Frontend** | React, Material UI | 사용자 대시보드 및 리포트 시각화 |
| **Backend** | Spring Boot (Java 17) | REST API 서버, 데이터 제공 및 사용자 관리 |
| **AI Crawler** | Python (Playwright) | 주요 커뮤니티 크롤링 및 데이터 수집 |
| **Database** | PostgreSQL | 수집 데이터 및 분석 결과 저장 |

## � 시작하기 (Getting Started)

### 1. 필수 요구사항
*   Docker & Docker Compose
*   Git

### 2. 설치 및 설정

프로젝트를 클론하고, 보안 설정 파일을 생성합니다.

```bash
# 저장소 클론
git clone https://github.com/bluevlad/TeacherHub.git
cd TeacherHub

# Docker Compose 설정 복사
copy docker-compose.example.yml docker-compose.yml

# Backend 설정 복사
copy backend\src\main\resources\application.properties.example backend\src\main\resources\application.properties
```

> **주의**: `docker-compose.yml` 및 `application.properties` 파일 내의 비밀번호(`CHANGEME`)를 실제 사용할 비밀번호로 변경하세요.

### 3. 호스트 파일 설정
로컬 테스트를 위해 운영 환경과 동일한 도메인으로 접속할 수 있도록 Hosts 파일을 수정해야 합니다.

*   **Windows**: `C:\Windows\System32\drivers\etc\hosts`
*   **Mac/Linux**: `/etc/hosts`

아래 내용을 추가합니다:
```text
127.0.0.1 teacherhub.unmong.com
```

### 4. 서비스 실행

Docker Compose를 사용하여 모든 서비스를 한 번에 실행합니다.

```bash
docker-compose up -d --build
```

## 🔌 접속 정보

서비스가 정상적으로 실행되면 아래 주소로 접속할 수 있습니다.

*   **Frontend (Dashboard)**: [http://teacherhub.unmong.com:3001](http://teacherhub.unmong.com:3001)
*   **Backend (API)**: [http://teacherhub.unmong.com:8081](http://teacherhub.unmong.com:8081)
*   **Database**: `localhost:5432`

> **참고**: 기존 포트(3000, 8080) 충돌을 방지하기 위해 TeacherHub는 **3001**과 **8081** 포트를 사용합니다.

## ✨ 주요 기능

1.  **데이터 수집 (Data Collection)**
    *   네이버/다음 카페, 디시인사이드 등 주요 커뮤니티 자동 크롤링
    *   키워드 기반 게시글 탐색

2.  **AI 감성 분석 (Sentiment Analysis)**
    *   한국어 자연어 처리(NLP)를 통한 긍정/부정/중립 판별
    *   주요 언급 키워드 추출

3.  **통합 대시보드**
    *   일간/주간/월간 여론 변화 추이 그래프
    *   부정 이슈 발생 시 실시간 알림

## 📁 프로젝트 구조

```
TeacherHub/
├── ai-crawler/          # Python 크롤러 및 AI 분석 모듈
├── backend/             # Spring Boot API 서버
├── database/            # DB 초기화 스크립트
├── frontend/            # React 대시보드
├── docker-compose.yml   # 전체 서비스 오케스트레이션
└── README.md
```

## � 라이선스

Copyright (c) 2024 **TeacherHub**. All rights reserved.
