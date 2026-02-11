"""
TeacherHub AI Crawler - V2 Entrypoint
Docker 컨테이너의 메인 엔트리포인트

실행 모드:
  full    - 스케줄러 + 크롤링 전체 실행 (운영 MacBook)
  ai-only - 스케줄러/크롤링 비활성화, DB 접속만 유지 (개발서버 AI 실험용)
"""
import argparse
import asyncio
import os
import sys
import time
import signal
import logging

from .logging_config import setup_logging
from .database import engine, init_db, SessionLocal
from .scheduler import TaskScheduler

logger = logging.getLogger(__name__)


def parse_args():
    """CLI 인자 파싱"""
    parser = argparse.ArgumentParser(description="TeacherHub AI Crawler V2")
    parser.add_argument(
        "--mode",
        choices=["full", "ai-only"],
        default=None,
        help="실행 모드: full(스케줄러), ai-only(DB 접속만)"
    )
    return parser.parse_args()


def get_app_mode(args) -> str:
    """실행 모드 결정 (CLI 인자 > 환경변수 > 기본값)"""
    if args.mode:
        return args.mode
    return os.getenv("APP_MODE", "full").lower()


def wait_for_db(max_retries: int = 30, retry_interval: int = 3):
    """DB 연결 대기 (retry 로직)"""
    from sqlalchemy import text

    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.warning(f"DB connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_interval)

    logger.error("Failed to connect to database after max retries")
    return False


async def run_initial_crawl():
    """초기 크롤링 1회 실행 (선택적)"""
    from .orchestrator import CrawlerOrchestrator

    naver_id = os.getenv("NAVER_ID")
    naver_pw = os.getenv("NAVER_PW")
    crawl_limit = int(os.getenv("CRAWL_LIMIT", "30"))

    db = SessionLocal()
    try:
        orchestrator = CrawlerOrchestrator(
            db=db,
            naver_id=naver_id,
            naver_pw=naver_pw
        )
        results = await orchestrator.crawl_all_sources(limit=crawl_limit)

        success_count = sum(1 for r in results if r['success'])
        total_posts = sum(r['posts_collected'] for r in results)
        logger.info(f"Initial crawl completed: {success_count}/{len(results)} sources, {total_posts} posts")

        return results
    except Exception as e:
        logger.error(f"Initial crawl failed: {e}")
        return []
    finally:
        db.close()


async def run_full_mode():
    """full 모드: 스케줄러 + 크롤링 전체 실행 (운영용)"""
    # 초기 크롤링 (환경 변수로 제어)
    run_initial = os.getenv("RUN_INITIAL_CRAWL", "false").lower() == "true"
    if run_initial:
        logger.info("Running initial crawl...")
        await run_initial_crawl()

    # 스케줄러 시작
    naver_id = os.getenv("NAVER_ID")
    naver_pw = os.getenv("NAVER_PW")
    crawl_limit = int(os.getenv("CRAWL_LIMIT", "50"))

    scheduler = TaskScheduler(
        naver_id=naver_id,
        naver_pw=naver_pw,
        crawl_limit=crawl_limit
    )
    scheduler.setup_default_jobs()
    scheduler.start()

    logger.info("Scheduler is running. Waiting for scheduled tasks...")

    # Graceful shutdown
    stop_event = asyncio.Event()

    def handle_signal(sig, frame):
        logger.info(f"Received signal {sig}. Shutting down...")
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.stop()


async def run_ai_only_mode():
    """ai-only 모드: DB 접속 유지, 스케줄러 비활성화 (개발서버 AI 실험용)"""
    logger.info("AI-Only mode: scheduler disabled, DB connection active")
    logger.info("Use CLI for manual operations: python -m src.cli crawl/report/status")

    # Graceful shutdown
    stop_event = asyncio.Event()

    def handle_signal(sig, frame):
        logger.info(f"Received signal {sig}. Shutting down...")
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass


async def main():
    """메인 실행 함수"""
    setup_logging()
    args = parse_args()
    mode = get_app_mode(args)

    logger.info("=" * 60)
    logger.info(f"TeacherHub AI Crawler V2 Starting... (mode={mode})")
    logger.info("=" * 60)

    # 1. DB 연결 대기
    if not wait_for_db():
        logger.error("Cannot start without database connection. Exiting.")
        sys.exit(1)

    # 2. DB 테이블 생성 확인
    try:
        init_db()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

    # 3. 모드별 실행
    if mode == "ai-only":
        await run_ai_only_mode()
    else:
        await run_full_mode()

    logger.info("TeacherHub AI Crawler stopped.")


if __name__ == "__main__":
    asyncio.run(main())
