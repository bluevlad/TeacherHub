# TeacherHub 문서 구조

## 디렉토리 구조

```
docs/
├── README.md                    # 이 파일 (문서 구조 설명)
├── IMPLEMENTATION_HISTORY.md    # 구현 히스토리
│
├── adr/                         # Architecture Decision Records
│   └── (설계 결정 기록)
│
├── api/                         # API 관련 문서
│   └── REPORT_API.md
│
├── dev/                         # 개발자 가이드
│   ├── SETUP.md
│   └── DEPLOYMENT.md
│
└── wiki/                        # GitHub Wiki 동기화용
    ├── Home.md
    ├── 1.-Project-Overview.md
    ├── 2.-Architecture.md
    ├── 3.-Domain-Model.md
    ├── 4.-API-Specification.md
    ├── 5.-Development-Guide.md
    └── 6.-Deployment.md
```

## 디렉토리 설명

| 디렉토리 | 용도 | 대상 |
|----------|------|------|
| `adr/` | 아키텍처 결정 기록 (Architecture Decision Records) | 개발자 |
| `api/` | API 명세, 변경 이력 | 개발자 |
| `dev/` | 개발 환경 설정, 배포, 트러블슈팅 | 개발자 |
| `wiki/` | GitHub Wiki 동기화 (공개 문서) | 모든 사용자 |

## 문서 작성 가이드

### 언제 어디에 작성할까?

| 상황 | 위치 | 예시 |
|------|------|------|
| 새 기능 설계 결정 | `adr/` | `adr/001-period-report-system.md` |
| API 변경/추가 | `api/` | `api/REPORT_API.md` |
| 개발 환경 변경 | `dev/` | `dev/SETUP.md` |
| 사용자 가이드 | `wiki/` | Wiki에서 직접 편집 권장 |

## Wiki 동기화

`wiki/` 폴더의 내용은 GitHub Wiki와 동기화됩니다.

```bash
# Wiki 저장소 클론
git clone https://github.com/bluevlad/TeacherHub.wiki.git

# 변경사항 복사
cp docs/wiki/* ../TeacherHub.wiki/

# 커밋 및 푸시
cd ../TeacherHub.wiki
git add . && git commit -m "docs: update wiki" && git push
```

## 관련 링크

- [GitHub Wiki](https://github.com/bluevlad/TeacherHub/wiki)
- [프로젝트 README](../README.md)
