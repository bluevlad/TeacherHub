#!/bin/bash
# ============================================
# TeacherHub - Windows Build & Export Script
# Windows에서 Docker 이미지 빌드 후 tar 파일로 내보내기
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXPORT_DIR="$SCRIPT_DIR/exports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 이미지 설정
IMAGE_PREFIX="research-hub"
IMAGES=(
    "teacherhub-api:backend"
    "teacherhub-front:frontend"
    "teacherhub-ai:ai-crawler"
)

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 사용법
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --all         모든 이미지 빌드 및 내보내기"
    echo "  --backend     Backend만 빌드"
    echo "  --frontend    Frontend만 빌드"
    echo "  --ai          AI Crawler만 빌드"
    echo "  --no-export   빌드만 수행 (내보내기 안함)"
    echo "  --help        도움말"
    echo ""
    echo "Examples:"
    echo "  $0 --all              # 전체 빌드 및 내보내기"
    echo "  $0 --backend --frontend  # Backend, Frontend만"
    echo ""
}

# Docker 확인
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되어 있지 않습니다."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker 데몬이 실행 중이 아닙니다."
        exit 1
    fi

    log_info "Docker 확인 완료"
}

# 이미지 빌드
build_image() {
    local name=$1
    local context=$2
    local full_name="${IMAGE_PREFIX}/${name}:latest"

    log_step "빌드 중: $full_name"

    cd "$PROJECT_ROOT/$context"
    docker build -t "$full_name" .

    log_info "빌드 완료: $full_name"
}

# 이미지 내보내기
export_image() {
    local name=$1
    local full_name="${IMAGE_PREFIX}/${name}:latest"
    local tar_file="$EXPORT_DIR/${name}_${TIMESTAMP}.tar"

    log_step "내보내기 중: $full_name -> $tar_file"

    docker save "$full_name" -o "$tar_file"

    # 파일 크기 확인
    local size=$(du -h "$tar_file" | cut -f1)
    log_info "내보내기 완료: $tar_file ($size)"
}

# 최신 심볼릭 링크 생성
create_latest_links() {
    log_step "최신 버전 링크 생성 중..."

    cd "$EXPORT_DIR"

    for img in "${IMAGES[@]}"; do
        local name="${img%%:*}"
        local latest_tar="${name}_${TIMESTAMP}.tar"
        local link_name="${name}_latest.tar"

        if [ -f "$latest_tar" ]; then
            rm -f "$link_name"
            ln -s "$latest_tar" "$link_name"
            log_info "링크 생성: $link_name -> $latest_tar"
        fi
    done
}

# 내보내기 디렉토리 정리 (7일 이상 된 파일 삭제)
cleanup_old_exports() {
    log_step "오래된 내보내기 파일 정리 중..."

    if [ -d "$EXPORT_DIR" ]; then
        find "$EXPORT_DIR" -name "*.tar" -mtime +7 -delete 2>/dev/null || true
        log_info "7일 이상 된 파일 삭제 완료"
    fi
}

# 요약 출력
print_summary() {
    echo ""
    echo "========================================"
    echo "빌드 및 내보내기 완료"
    echo "========================================"
    echo ""
    echo "내보내기 디렉토리: $EXPORT_DIR"
    echo ""
    echo "생성된 파일:"
    ls -lh "$EXPORT_DIR"/*_${TIMESTAMP}.tar 2>/dev/null || echo "  (없음)"
    echo ""
    echo "다음 단계:"
    echo "  1. 파일을 MacBook으로 전송:"
    echo "     scp $EXPORT_DIR/*_latest.tar user@172.30.1.100:~/transfers/"
    echo ""
    echo "  2. MacBook에서 import-and-run.sh 실행"
    echo ""
}

# 메인
main() {
    local build_backend=false
    local build_frontend=false
    local build_ai=false
    local do_export=true

    # 파라미터 없으면 도움말
    if [ $# -eq 0 ]; then
        usage
        exit 0
    fi

    # 파라미터 파싱
    for arg in "$@"; do
        case $arg in
            --all)
                build_backend=true
                build_frontend=true
                build_ai=true
                ;;
            --backend)
                build_backend=true
                ;;
            --frontend)
                build_frontend=true
                ;;
            --ai)
                build_ai=true
                ;;
            --no-export)
                do_export=false
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                log_error "알 수 없는 옵션: $arg"
                usage
                exit 1
                ;;
        esac
    done

    echo ""
    echo "========================================"
    echo "TeacherHub 빌드 및 내보내기"
    echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""

    # Docker 확인
    check_docker

    # 내보내기 디렉토리 생성
    mkdir -p "$EXPORT_DIR"

    # 빌드
    if [ "$build_backend" = true ]; then
        build_image "teacherhub-api" "backend"
        [ "$do_export" = true ] && export_image "teacherhub-api"
    fi

    if [ "$build_frontend" = true ]; then
        build_image "teacherhub-front" "frontend"
        [ "$do_export" = true ] && export_image "teacherhub-front"
    fi

    if [ "$build_ai" = true ]; then
        build_image "teacherhub-ai" "ai-crawler"
        [ "$do_export" = true ] && export_image "teacherhub-ai"
    fi

    # 후처리
    if [ "$do_export" = true ]; then
        create_latest_links
        cleanup_old_exports
        print_summary
    else
        log_info "빌드 완료 (내보내기 생략)"
    fi
}

main "$@"
