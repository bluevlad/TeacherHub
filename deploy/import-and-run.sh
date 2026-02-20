#!/bin/bash
# ============================================
# TeacherHub - MacBook Import & Run Script
# MacBook (OrbStack)에서 이미지 가져오기 및 실행
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IMPORT_DIR="${IMPORT_DIR:-$HOME/transfers}"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 이미지 설정
IMAGE_PREFIX="research-hub"
IMAGES=(
    "teacherhub-api"
    "teacherhub-front"
    "teacherhub-ai"
)

# 컨테이너 설정
CONTAINERS=(
    "teacherhub-frontend-prod"
    "teacherhub-backend-prod"
    "teacherhub-ai-prod"
    "teacherhub-db-prod"
)

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 사용법
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  import        tar 파일에서 이미지 가져오기"
    echo "  start         서비스 시작"
    echo "  stop          서비스 중지"
    echo "  restart       서비스 재시작"
    echo "  status        서비스 상태 확인"
    echo "  logs          로그 확인"
    echo "  full-deploy   전체 배포 (import + start)"
    echo ""
    echo "Options:"
    echo "  --from=DIR    tar 파일 디렉토리 (기본: ~/transfers)"
    echo ""
    echo "Examples:"
    echo "  $0 import                     # 이미지 가져오기"
    echo "  $0 start                      # 서비스 시작"
    echo "  $0 full-deploy                # 전체 배포"
    echo "  $0 import --from=/tmp/images  # 다른 디렉토리에서"
    echo ""
}

# Docker/OrbStack 확인
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker CLI가 설치되어 있지 않습니다."
        log_info "OrbStack 설정에서 'Install Docker CLI'를 실행하세요."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker/OrbStack이 실행 중이 아닙니다."
        exit 1
    fi

    log_info "Docker/OrbStack 확인 완료"
}

# 이미지 가져오기
import_images() {
    log_step "이미지 가져오기 시작..."

    if [ ! -d "$IMPORT_DIR" ]; then
        log_error "디렉토리를 찾을 수 없습니다: $IMPORT_DIR"
        exit 1
    fi

    local imported=0

    for img in "${IMAGES[@]}"; do
        # _latest.tar 또는 가장 최근 파일 찾기
        local tar_file="$IMPORT_DIR/${img}_latest.tar"

        if [ ! -f "$tar_file" ]; then
            # latest가 없으면 가장 최근 파일 찾기
            tar_file=$(ls -t "$IMPORT_DIR/${img}_"*.tar 2>/dev/null | head -1)
        fi

        if [ -f "$tar_file" ]; then
            log_step "가져오기: $tar_file"
            docker load -i "$tar_file"
            ((imported++))
            log_info "완료: ${IMAGE_PREFIX}/${img}:latest"
        else
            log_warn "파일 없음: ${img}_*.tar"
        fi
    done

    if [ $imported -eq 0 ]; then
        log_error "가져올 이미지 파일이 없습니다."
        log_info "Windows에서 build-and-export.sh를 먼저 실행하세요."
        exit 1
    fi

    log_info "총 $imported 개 이미지 가져오기 완료"
}

# 기존 컨테이너 중지 및 제거
stop_containers() {
    log_step "기존 컨테이너 중지 중..."

    for container in "${CONTAINERS[@]}"; do
        if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
            docker stop "$container" 2>/dev/null || true
            docker rm "$container" 2>/dev/null || true
            log_info "제거됨: $container"
        fi
    done
}

# 서비스 시작
start_services() {
    log_step "서비스 시작 중..."

    cd "$PROJECT_ROOT"

    # .env 파일 확인
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        if [ -f "$SCRIPT_DIR/.env.template" ]; then
            log_warn ".env 파일이 없습니다. 템플릿에서 복사합니다."
            cp "$SCRIPT_DIR/.env.template" "$SCRIPT_DIR/.env"
            log_warn ".env 파일을 확인하고 필요시 수정하세요."
        fi
    fi

    # docker-compose 실행
    docker compose -f docker-compose.prod.yml up -d

    log_info "서비스 시작 완료"
    show_status
}

# 서비스 중지
stop_services() {
    log_step "서비스 중지 중..."

    cd "$PROJECT_ROOT"
    docker compose -f docker-compose.prod.yml down

    log_info "서비스 중지 완료"
}

# 서비스 재시작
restart_services() {
    stop_services
    sleep 2
    start_services
}

# 상태 확인
show_status() {
    echo ""
    log_info "=== 컨테이너 상태 ==="
    docker ps --filter "name=teacherhub" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    log_info "=== 접속 URL ==="
    echo "  Frontend: http://localhost:4010"
    echo "  Backend:  http://localhost:9010"
    echo ""
}

# 로그 확인
show_logs() {
    local service="$1"

    cd "$PROJECT_ROOT"

    if [ -z "$service" ]; then
        docker compose -f docker-compose.prod.yml logs -f --tail=100
    else
        docker compose -f docker-compose.prod.yml logs -f --tail=100 "$service"
    fi
}

# 전체 배포
full_deploy() {
    echo ""
    echo "========================================"
    echo "TeacherHub 전체 배포"
    echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""

    check_docker
    import_images
    stop_containers
    start_services

    echo ""
    echo "========================================"
    echo "배포 완료!"
    echo "========================================"
}

# 메인
main() {
    local command="$1"
    shift || true

    # 파라미터 파싱
    for arg in "$@"; do
        case $arg in
            --from=*)
                IMPORT_DIR="${arg#*=}"
                ;;
        esac
    done

    case "$command" in
        import)
            check_docker
            import_images
            ;;
        start)
            check_docker
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_docker
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$1"
            ;;
        full-deploy)
            full_deploy
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"
