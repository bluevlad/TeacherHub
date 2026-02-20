#!/bin/bash
# ============================================
# TeacherHub - Database Backup Script
# PostgreSQL 데이터베이스 백업
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 설정
DB_CONTAINER="${DB_CONTAINER:-teacherhub-db-prod}"
DB_NAME="${DB_NAME:-teacherhub}"
DB_USER="${DB_USER:-teacherhub}"

# Windows용 컨테이너 이름 (개발환경)
DB_CONTAINER_DEV="teacherhub-db"

# 사용법
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --dev         개발 환경 (Windows)"
    echo "  --prod        운영 환경 (MacBook)"
    echo "  --container=  컨테이너 이름 지정"
    echo "  --output=     출력 파일 경로"
    echo ""
    echo "Examples:"
    echo "  $0 --dev      # Windows 개발환경 백업"
    echo "  $0 --prod     # MacBook 운영환경 백업"
    echo ""
}

# 컨테이너 확인
check_container() {
    local container=$1

    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        log_error "컨테이너를 찾을 수 없습니다: $container"
        echo ""
        echo "실행 중인 PostgreSQL 컨테이너:"
        docker ps --filter "ancestor=postgres" --format "  {{.Names}}"
        exit 1
    fi
}

# 백업 실행
backup_database() {
    local container=$1
    local output_file=$2

    log_info "백업 시작..."
    log_info "  컨테이너: $container"
    log_info "  데이터베이스: $DB_NAME"
    log_info "  출력 파일: $output_file"

    # 백업 디렉토리 생성
    mkdir -p "$(dirname "$output_file")"

    # pg_dump 실행
    docker exec "$container" pg_dump -U "$DB_USER" -d "$DB_NAME" \
        --no-owner --no-acl > "$output_file"

    # 결과 확인
    if [ -f "$output_file" ]; then
        local size=$(du -h "$output_file" | cut -f1)
        local lines=$(wc -l < "$output_file")
        log_info "백업 완료!"
        log_info "  파일 크기: $size"
        log_info "  라인 수: $lines"
    else
        log_error "백업 파일 생성 실패"
        exit 1
    fi
}

# 압축
compress_backup() {
    local file=$1

    if command -v gzip &> /dev/null; then
        log_info "백업 파일 압축 중..."
        gzip -f "$file"
        log_info "압축 완료: ${file}.gz"
    fi
}

# 오래된 백업 정리
cleanup_old_backups() {
    log_info "오래된 백업 파일 정리 중..."

    # 7일 이상 된 파일 삭제
    find "$BACKUP_DIR" -name "teacherhub_*.sql*" -mtime +7 -delete 2>/dev/null || true

    # 최근 10개만 유지
    local count=$(ls -1 "$BACKUP_DIR"/teacherhub_*.sql* 2>/dev/null | wc -l)
    if [ "$count" -gt 10 ]; then
        ls -1t "$BACKUP_DIR"/teacherhub_*.sql* | tail -n +11 | xargs rm -f
        log_info "10개 초과 백업 삭제"
    fi

    log_info "정리 완료"
}

# 메인
main() {
    local container="$DB_CONTAINER"
    local output_file="$BACKUP_DIR/teacherhub_${TIMESTAMP}.sql"

    # 파라미터 파싱
    for arg in "$@"; do
        case $arg in
            --dev)
                container="$DB_CONTAINER_DEV"
                ;;
            --prod)
                container="$DB_CONTAINER"
                ;;
            --container=*)
                container="${arg#*=}"
                ;;
            --output=*)
                output_file="${arg#*=}"
                ;;
            --help|-h)
                usage
                exit 0
                ;;
        esac
    done

    echo ""
    echo "========================================"
    echo "TeacherHub 데이터베이스 백업"
    echo "시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""

    check_container "$container"
    backup_database "$container" "$output_file"
    compress_backup "$output_file"
    cleanup_old_backups

    echo ""
    echo "========================================"
    echo "백업 완료!"
    echo ""
    echo "MacBook으로 전송:"
    echo "  scp ${output_file}.gz user@172.30.1.100:~/transfers/"
    echo "========================================"
}

main "$@"
