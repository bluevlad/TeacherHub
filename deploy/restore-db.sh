#!/bin/bash
# ============================================
# TeacherHub - Database Restore Script
# PostgreSQL 데이터베이스 복원
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
IMPORT_DIR="${IMPORT_DIR:-$HOME/transfers}"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 설정
DB_CONTAINER="${DB_CONTAINER:-teacherhub-db-prod}"
DB_NAME="${DB_NAME:-teacherhub}"
DB_USER="${DB_USER:-teacherhub}"

# 사용법
usage() {
    echo "Usage: $0 [options] [backup_file]"
    echo ""
    echo "Options:"
    echo "  --container=  컨테이너 이름 지정"
    echo "  --from=       백업 파일 디렉토리"
    echo "  --latest      가장 최근 백업 사용"
    echo "  --force       확인 없이 진행"
    echo ""
    echo "Examples:"
    echo "  $0 --latest                    # 최근 백업으로 복원"
    echo "  $0 backup.sql                  # 지정 파일로 복원"
    echo "  $0 --from=~/transfers backup.sql.gz"
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

# 백업 파일 찾기
find_backup_file() {
    local search_dir=$1
    local latest=${2:-false}

    if [ "$latest" = true ]; then
        # 가장 최근 파일 찾기
        local file=$(ls -t "$search_dir"/teacherhub_*.sql* 2>/dev/null | head -1)

        if [ -z "$file" ]; then
            # transfers 디렉토리에서도 찾기
            file=$(ls -t "$IMPORT_DIR"/teacherhub_*.sql* 2>/dev/null | head -1)
        fi

        echo "$file"
    fi
}

# 파일 압축 해제
decompress_if_needed() {
    local file=$1

    if [[ "$file" == *.gz ]]; then
        log_step "압축 해제 중: $file"

        local unzipped="${file%.gz}"
        gunzip -k -f "$file"

        echo "$unzipped"
    else
        echo "$file"
    fi
}

# 데이터베이스 복원
restore_database() {
    local container=$1
    local backup_file=$2

    log_step "데이터베이스 복원 시작..."
    log_info "  컨테이너: $container"
    log_info "  백업 파일: $backup_file"

    # 파일을 컨테이너에 복사
    local container_path="/tmp/restore_backup.sql"
    docker cp "$backup_file" "${container}:${container_path}"

    # 기존 데이터 삭제 (선택적)
    log_step "기존 테이블 정리 중..."
    docker exec "$container" psql -U "$DB_USER" -d "$DB_NAME" -c "
        DO \$\$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END \$\$;
    " 2>/dev/null || true

    # 복원 실행
    log_step "데이터 복원 중..."
    docker exec "$container" psql -U "$DB_USER" -d "$DB_NAME" -f "$container_path"

    # 임시 파일 삭제
    docker exec "$container" rm -f "$container_path"

    log_info "복원 완료!"
}

# 복원 결과 확인
verify_restore() {
    local container=$1

    log_step "복원 결과 확인..."

    echo ""
    echo "=== 테이블 목록 ==="
    docker exec "$container" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    "

    echo ""
    echo "=== 주요 테이블 레코드 수 ==="
    docker exec "$container" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 'teachers' as table_name, COUNT(*) as count FROM teachers
        UNION ALL
        SELECT 'academies', COUNT(*) FROM academies
        UNION ALL
        SELECT 'posts', COUNT(*) FROM posts
        UNION ALL
        SELECT 'teacher_mentions', COUNT(*) FROM teacher_mentions
        UNION ALL
        SELECT 'daily_reports', COUNT(*) FROM daily_reports;
    " 2>/dev/null || log_warn "일부 테이블이 없을 수 있습니다."
}

# 메인
main() {
    local container="$DB_CONTAINER"
    local backup_file=""
    local search_dir="$BACKUP_DIR"
    local use_latest=false
    local force=false

    # 파라미터 파싱
    for arg in "$@"; do
        case $arg in
            --container=*)
                container="${arg#*=}"
                ;;
            --from=*)
                search_dir="${arg#*=}"
                ;;
            --latest)
                use_latest=true
                ;;
            --force)
                force=true
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            *)
                if [ -z "$backup_file" ] && [[ ! "$arg" == --* ]]; then
                    backup_file="$arg"
                fi
                ;;
        esac
    done

    echo ""
    echo "========================================"
    echo "TeacherHub 데이터베이스 복원"
    echo "시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""

    # 백업 파일 결정
    if [ "$use_latest" = true ]; then
        backup_file=$(find_backup_file "$search_dir" true)
    elif [ -n "$backup_file" ] && [ ! -f "$backup_file" ]; then
        # 상대 경로면 search_dir에서 찾기
        if [ -f "$search_dir/$backup_file" ]; then
            backup_file="$search_dir/$backup_file"
        elif [ -f "$IMPORT_DIR/$backup_file" ]; then
            backup_file="$IMPORT_DIR/$backup_file"
        fi
    fi

    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        log_error "백업 파일을 찾을 수 없습니다."
        echo ""
        echo "사용 가능한 백업 파일:"
        ls -lt "$BACKUP_DIR"/teacherhub_*.sql* 2>/dev/null | head -5 || echo "  (없음)"
        ls -lt "$IMPORT_DIR"/teacherhub_*.sql* 2>/dev/null | head -5 || true
        echo ""
        usage
        exit 1
    fi

    # 컨테이너 확인
    check_container "$container"

    # 확인 메시지
    if [ "$force" != true ]; then
        echo ""
        log_warn "주의: 기존 데이터가 삭제됩니다!"
        echo ""
        echo "  컨테이너: $container"
        echo "  백업 파일: $backup_file"
        echo ""
        read -p "계속하시겠습니까? (y/N): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log_info "취소되었습니다."
            exit 0
        fi
    fi

    # 압축 해제
    backup_file=$(decompress_if_needed "$backup_file")

    # 복원 실행
    restore_database "$container" "$backup_file"

    # 결과 확인
    verify_restore "$container"

    echo ""
    echo "========================================"
    echo "복원 완료!"
    echo "========================================"
}

main "$@"
