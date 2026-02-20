# TeacherHub MacBook 배포 가이드

Windows 개발 환경에서 MacBook OrbStack 운영 환경으로 배포하는 가이드입니다.

## 환경 정보

| 항목 | Windows (개발) | MacBook (운영) |
|------|---------------|----------------|
| IP | 172.30.1.78 | 172.30.1.100 |
| Docker | Docker Desktop | OrbStack |
| Frontend | localhost:3000 | :4010 |
| Backend | localhost:8081 | :9010 |

## 배포 스크립트

| 스크립트 | 실행 위치 | 설명 |
|----------|----------|------|
| `build-and-export.sh` | Windows | 이미지 빌드 및 tar 내보내기 |
| `import-and-run.sh` | MacBook | 이미지 가져오기 및 실행 |
| `backup-db.sh` | 양쪽 | PostgreSQL 백업 |
| `restore-db.sh` | MacBook | PostgreSQL 복원 |

---

## 전체 배포 절차

### Step 1: Windows에서 이미지 빌드 및 내보내기

```bash
cd C:\GIT\TeacherHub\deploy

# 전체 빌드 및 내보내기
./build-and-export.sh --all

# 또는 선택적 빌드
./build-and-export.sh --backend --frontend
```

**결과물:**
```
deploy/exports/
├── teacherhub-api_20260204_143000.tar
├── teacherhub-api_latest.tar -> teacherhub-api_20260204_143000.tar
├── teacherhub-front_20260204_143000.tar
├── teacherhub-front_latest.tar -> ...
├── teacherhub-ai_20260204_143000.tar
└── teacherhub-ai_latest.tar -> ...
```

### Step 2: 데이터베이스 백업 (Windows)

```bash
# 개발 환경 DB 백업
./backup-db.sh --dev

# 결과: deploy/backups/teacherhub_20260204_143000.sql.gz
```

### Step 3: MacBook으로 파일 전송

```bash
# scp로 전송
scp deploy/exports/*_latest.tar user@172.30.1.100:~/transfers/
scp deploy/backups/teacherhub_*.sql.gz user@172.30.1.100:~/transfers/

# 또는 공유 폴더 사용
cp deploy/exports/*_latest.tar /path/to/shared/folder/
```

### Step 4: MacBook에서 이미지 가져오기 및 실행

```bash
cd ~/projects/TeacherHub/deploy

# 전체 배포 (이미지 가져오기 + 서비스 시작)
./import-and-run.sh full-deploy

# 또는 단계별 실행
./import-and-run.sh import      # 이미지만 가져오기
./import-and-run.sh start       # 서비스 시작
```

### Step 5: 데이터베이스 복원 (MacBook)

```bash
# 최근 백업으로 복원
./restore-db.sh --latest

# 또는 특정 파일 지정
./restore-db.sh --from=~/transfers teacherhub_20260204_143000.sql.gz
```

---

## 빠른 배포 (한 줄 명령)

### Windows에서
```bash
cd C:\GIT\TeacherHub\deploy && \
./build-and-export.sh --all && \
./backup-db.sh --dev && \
scp exports/*_latest.tar backups/*.sql.gz user@172.30.1.100:~/transfers/
```

### MacBook에서
```bash
cd ~/projects/TeacherHub/deploy && \
./import-and-run.sh full-deploy && \
./restore-db.sh --latest --force
```

---

## 스크립트 상세 사용법

### build-and-export.sh

```bash
# 사용법
./build-and-export.sh [options]

# 옵션
--all         모든 이미지 빌드 및 내보내기
--backend     Backend만 빌드
--frontend    Frontend만 빌드
--ai          AI Crawler만 빌드
--no-export   빌드만 수행 (내보내기 안함)

# 예시
./build-and-export.sh --all              # 전체
./build-and-export.sh --backend          # Backend만
./build-and-export.sh --frontend --ai    # Frontend + AI
```

### import-and-run.sh

```bash
# 사용법
./import-and-run.sh [command] [options]

# 명령
import        tar 파일에서 이미지 가져오기
start         서비스 시작
stop          서비스 중지
restart       서비스 재시작
status        서비스 상태 확인
logs          로그 확인
full-deploy   전체 배포 (import + start)

# 옵션
--from=DIR    tar 파일 디렉토리 (기본: ~/transfers)

# 예시
./import-and-run.sh full-deploy
./import-and-run.sh import --from=/tmp/images
./import-and-run.sh logs backend
```

### backup-db.sh

```bash
# 사용법
./backup-db.sh [options]

# 옵션
--dev         개발 환경 (Windows Docker)
--prod        운영 환경 (MacBook OrbStack)
--container=  컨테이너 이름 지정
--output=     출력 파일 경로

# 예시
./backup-db.sh --dev     # Windows
./backup-db.sh --prod    # MacBook
```

### restore-db.sh

```bash
# 사용법
./restore-db.sh [options] [backup_file]

# 옵션
--container=  컨테이너 이름 지정
--from=       백업 파일 디렉토리
--latest      가장 최근 백업 사용
--force       확인 없이 진행

# 예시
./restore-db.sh --latest
./restore-db.sh --from=~/transfers teacherhub_backup.sql.gz
./restore-db.sh --latest --force
```

---

## 문제 해결

### Docker CLI를 찾을 수 없음 (MacBook)

```bash
# OrbStack Docker CLI 설정
export PATH="$HOME/.orbstack/bin:$PATH"
echo 'export PATH="$HOME/.orbstack/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 이미지 파일을 찾을 수 없음

```bash
# 전송된 파일 확인
ls -la ~/transfers/

# 다른 위치에서 가져오기
./import-and-run.sh import --from=/path/to/files
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
lsof -i :4010
lsof -i :9010

# 기존 컨테이너 정리
docker stop teacherhub-frontend-prod teacherhub-backend-prod
docker rm teacherhub-frontend-prod teacherhub-backend-prod
```

### 데이터베이스 연결 실패

```bash
# DB 컨테이너 상태 확인
docker logs teacherhub-db-prod

# DB 연결 테스트
docker exec teacherhub-db-prod psql -U teacherhub -d teacherhub -c "SELECT 1"
```

---

## 서비스 접속

| 서비스 | URL |
|--------|-----|
| Frontend | http://localhost:4010 |
| Backend API | http://localhost:9010 |
| Health Check | http://localhost:9010/actuator/health |

---

## 관련 문서

- [포트 정책](../../Claude-Opus-bluevlad/services/PORTS.md)
- [서비스 README](../../Claude-Opus-bluevlad/services/teacherhub/README.md)
- [구현 히스토리](../docs/IMPLEMENTATION_HISTORY.md)
