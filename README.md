# TeacherHub

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/status-Active-success.svg" alt="Status">
</p>

> **공무원 학원 강사 평판 분석 시스템**

TeacherHub는 디시인사이드 공무원 갤러리에서 강사 관련 게시글을 자동 수집하고, AI 감성 분석을 통해 긍정/부정/중립을 판별하여 일별/주별/월별 통계 대시보드를 제공하는 플랫폼입니다.

---

## 핵심 기능

| 기능 | 설명 |
|------|------|
| **데이터 수집** | 커뮤니티 게시글 자동 크롤링 |
| **감성 분석** | AI 기반 긍정/부정/중립 분류 |
| **기간별 통계** | 일별/주별/월별 트렌드 조회 |
| **강사 랭킹** | 언급량, 긍정도 기준 순위 |

---

## 기술 스택

| 서비스 | 기술 |
|--------|------|
| Frontend | React, Material UI |
| Backend | Spring Boot 3.2, Java 17 |
| AI Crawler | Python, Playwright, TextBlob |
| Database | PostgreSQL 15 |
| Infrastructure | Docker, GitHub Actions |

---

## 빠른 시작

```bash
# 저장소 클론
git clone https://github.com/bluevlad/TeacherHub.git
cd TeacherHub

# 서비스 실행
docker-compose up -d

# 접속
# Frontend: http://localhost:3000
# Backend:  http://localhost:8081
```

---

## 문서

상세 문서는 아래 링크에서 확인할 수 있습니다.

| 문서 | 설명 |
|------|------|
| [GitHub Wiki](https://github.com/bluevlad/TeacherHub/wiki) | 전체 프로젝트 문서 |
| [docs/](./docs/) | 로컬 문서 저장소 |

### Wiki 목차

- [1. 프로젝트 개요](https://github.com/bluevlad/TeacherHub/wiki/1.-Project-Overview) - 비전, 목표, 핵심 가치
- [2. 아키텍처](https://github.com/bluevlad/TeacherHub/wiki/2.-Architecture) - 시스템 구조, 기술 스택
- [3. 도메인 모델](https://github.com/bluevlad/TeacherHub/wiki/3.-Domain-Model) - 엔티티, ER 다이어그램
- [4. API 명세](https://github.com/bluevlad/TeacherHub/wiki/4.-API-Specification) - REST API 문서
- [5. 개발 가이드](https://github.com/bluevlad/TeacherHub/wiki/5.-Development-Guide) - 환경 설정, 컨벤션
- [6. 배포](https://github.com/bluevlad/TeacherHub/wiki/6.-Deployment) - CI/CD, 인프라

---

## 프로젝트 구조

```
TeacherHub/
├── backend/         # Spring Boot API 서버
├── frontend/        # React 대시보드
├── ai-crawler/      # Python 크롤러
├── deploy/          # 배포 스크립트
├── docs/            # 문서
└── docker-compose.yml
```

---

## 라이선스

MIT License - Copyright (c) 2024-2026 TeacherHub
