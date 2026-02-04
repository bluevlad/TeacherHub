# TeacherHub

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/status-Active-success.svg" alt="Status">
</p>

> **공무원 학원 강사 평판 분석 시스템**

TeacherHub는 디시인사이드 공무원 갤러리에서 강사 관련 게시글을 크롤링하여 감성 분석을 수행하고, 일별/주별/월별 통계를 제공하는 플랫폼입니다.

---

## 목차

| 섹션 | 설명 |
|------|------|
| [1. 프로젝트 개요](./1.-Project-Overview) | 비전, 목표, 핵심 가치 |
| [2. 아키텍처](./2.-Architecture) | 시스템 구조, 기술 스택 |
| [3. 도메인 모델](./3.-Domain-Model) | 엔티티, ER 다이어그램 |
| [4. API 명세](./4.-API-Specification) | REST API 문서 |
| [5. 개발 가이드](./5.-Development-Guide) | 환경 설정, 컨벤션 |
| [6. 배포](./6.-Deployment) | CI/CD, 인프라 |

---

## 핵심 기능

### 데이터 수집
| 기능 | 설명 |
|------|------|
| **웹 크롤링** | 디시인사이드 공무원 갤러리 게시글 수집 |
| **강사 언급 추출** | 등록된 강사명 기반 언급 탐지 |
| **감성 분석** | 긍정/부정/중립 분류 |
| **일일 리포트** | 일별 집계 데이터 생성 |

### 분석 대시보드
| 기능 | 설명 |
|------|------|
| **기간별 조회** | 일별/주별/월별 통계 조회 |
| **강사 랭킹** | 언급량, 긍정도 기준 순위 |
| **트렌드 분석** | 시간에 따른 평판 변화 추적 |

---

## 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
├─────────────────────────────────────────────────────────────┤
│                    React Dashboard                          │
│                   (Material UI)                             │
├─────────────────────────────────────────────────────────────┤
│                      Backend (Spring Boot)                  │
├──────────────────────┬──────────────────────────────────────┤
│   /api/v2/reports/*  │         /api/teachers/*              │
│   Period Reports     │         Teacher Management           │
├──────────────────────┴──────────────────────────────────────┤
│                     Data Layer                              │
├─────────────────────────┬───────────────────────────────────┤
│     PostgreSQL          │       AI Crawler (Python)         │
│     (daily_reports)     │       (Playwright + TextBlob)     │
└─────────────────────────┴───────────────────────────────────┘
```

---

## 기술 스택

### Backend
| 기술 | 버전 | 용도 |
|------|------|------|
| Java | 17+ | 런타임 |
| Spring Boot | 3.2+ | Web Framework |
| Spring Data JPA | - | ORM |
| PostgreSQL | 15+ | Database |

### Frontend
| 기술 | 버전 | 용도 |
|------|------|------|
| React | 18+ | UI Framework |
| Material UI | 5+ | Component Library |
| Axios | 1+ | HTTP Client |

### AI Crawler
| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.10+ | 런타임 |
| Playwright | 1.40+ | 웹 크롤링 |
| TextBlob | 0.18+ | 감성 분석 |
| SQLAlchemy | 2.0+ | ORM |

### Infrastructure
| 기술 | 용도 |
|------|------|
| Docker | 컨테이너화 |
| Docker Compose | 로컬/운영 환경 |
| GitHub Actions | CI/CD |
| OrbStack | MacBook 운영 환경 |

---

## 빠른 시작

### 사전 요구사항
- Docker & Docker Compose
- Git

### 실행 방법
```bash
# 1. 저장소 클론
git clone https://github.com/bluevlad/TeacherHub.git
cd TeacherHub

# 2. 서비스 시작 (개발)
docker-compose up -d

# 3. 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:8081
```

---

## 프로젝트 현황

### 버전 정보
| 버전 | 상태 | 주요 변경사항 |
|------|------|---------------|
| v1.0.0 | **현재** | 기간별 조회 기능 (일별/주별/월별) |
| v0.9.0 | 완료 | 기본 대시보드, 크롤링 시스템 |

### 개발 현황
| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | 크롤링 및 감성 분석 | 완료 |
| Phase 2 | 기간별 조회 시스템 | 완료 |
| Phase 3 | MacBook 배포 자동화 | 완료 |
| Phase 4 | 트렌드 차트 | 예정 |

---

## 프로젝트 구조

```
TeacherHub/
├── backend/
│   └── src/main/java/com/teacherhub/
│       ├── controller/        # REST Controllers
│       ├── dto/               # Data Transfer Objects
│       ├── entity/            # JPA Entities
│       ├── repository/        # Data Access Layer
│       └── service/           # Business Logic
├── frontend/
│   └── src/
│       ├── api/               # API Client
│       ├── components/        # Reusable Components
│       └── pages/             # Page Components
├── ai-crawler/
│   └── src/
│       ├── crawlers/          # Site Crawlers
│       └── analyzers/         # Sentiment Analysis
├── deploy/                    # Deployment Scripts
├── docs/                      # Documentation
└── docker-compose.yml
```

---

## 관련 링크

| 링크 | 설명 |
|------|------|
| [GitHub Repository](https://github.com/bluevlad/TeacherHub) | 소스 코드 |
| [Issue Tracker](https://github.com/bluevlad/TeacherHub/issues) | 버그 리포트 / 기능 요청 |

---

## 팀

| 역할 | 담당 |
|------|------|
| Project Owner | bluevlad |
| Development | Claude Code (AI Assistant) |

---

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

<p align="center">
  <sub>© 2024-2026 TeacherHub. All rights reserved.</sub>
</p>
