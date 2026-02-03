#!/bin/bash
# ============================================
# TeacherHub Deployment Script
# 운영 서버 배포 스크립트
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 사용법 출력
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start       - 서비스 시작"
    echo "  stop        - 서비스 중지"
    echo "  restart     - 서비스 재시작"
    echo "  status      - 서비스 상태 확인"
    echo "  logs        - 로그 확인"
    echo "  migrate     - DB 마이그레이션 실행"
    echo "  backup      - DB 백업"
    echo "  update      - 코드 업데이트 및 재배포"
    echo ""
    echo "Options:"
    echo "  --env=dev|staging|prod  - 환경 지정 (기본: prod)"
    echo ""
}

# 환경 설정 로드
load_env() {
    local env_file="$SCRIPT_DIR/.env"

    if [ ! -f "$env_file" ]; then
        log_error ".env 파일이 없습니다. .env.template을 복사하여 설정하세요."
        exit 1
    fi

    source "$env_file"
    log_info "환경 설정 로드 완료: $ENV"
}

# 서비스 시작
start_services() {
    log_info "서비스 시작 중..."
    cd "$SCRIPT_DIR"

    if [ "$ENV" == "production" ]; then
        docker-compose --profile production up -d
    else
        docker-compose up -d
    fi

    log_info "서비스 시작 완료"
    show_status
}

# 서비스 중지
stop_services() {
    log_info "서비스 중지 중..."
    cd "$SCRIPT_DIR"
    docker-compose down
    log_info "서비스 중지 완료"
}

# 서비스 재시작
restart_services() {
    stop_services
    start_services
}

# 상태 확인
show_status() {
    log_info "서비스 상태:"
    cd "$SCRIPT_DIR"
    docker-compose ps
}

# 로그 확인
show_logs() {
    local service="$1"
    cd "$SCRIPT_DIR"

    if [ -z "$service" ]; then
        docker-compose logs -f --tail=100
    else
        docker-compose logs -f --tail=100 "$service"
    fi
}

# DB 마이그레이션
run_migration() {
    log_info "DB 마이그레이션 실행 중..."
    cd "$SCRIPT_DIR"

    # 마이그레이션 파일 실행
    for file in "$PROJECT_ROOT/database/migrations"/*.sql; do
        if [ -f "$file" ]; then
            log_info "실행: $(basename $file)"
            docker-compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -f "/docker-entrypoint-initdb.d/$(basename $file)"
        fi
    done

    log_info "마이그레이션 완료"
}

# DB 백업
backup_db() {
    local backup_dir="$SCRIPT_DIR/backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/teacherhub_$timestamp.sql"

    mkdir -p "$backup_dir"

    log_info "DB 백업 중: $backup_file"
    cd "$SCRIPT_DIR"
    docker-compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$backup_file"

    # 압축
    gzip "$backup_file"
    log_info "백업 완료: ${backup_file}.gz"

    # 7일 이상 된 백업 삭제
    find "$backup_dir" -name "*.sql.gz" -mtime +7 -delete
    log_info "오래된 백업 정리 완료"
}

# 코드 업데이트 및 재배포
update_and_deploy() {
    log_info "코드 업데이트 중..."
    cd "$PROJECT_ROOT"

    # Git pull
    git fetch origin
    git pull origin master

    log_info "이미지 빌드 중..."
    cd "$SCRIPT_DIR"
    docker-compose build --no-cache

    log_info "서비스 재시작 중..."
    docker-compose up -d

    log_info "업데이트 및 배포 완료"
    show_status
}

# 메인 로직
main() {
    local command="$1"
    shift || true

    # 환경 파라미터 파싱
    for arg in "$@"; do
        case $arg in
            --env=*)
                ENV="${arg#*=}"
                ;;
        esac
    done

    load_env

    case "$command" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        migrate)
            run_migration
            ;;
        backup)
            backup_db
            ;;
        update)
            update_and_deploy
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"
