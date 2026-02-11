"""
Task Scheduler
자동화된 크롤링 및 리포트 생성 스케줄러
"""
import asyncio
import logging
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .database import SessionLocal
from .orchestrator import CrawlerOrchestrator
from .services.report_generator import ReportGenerator
from .services.weekly_aggregator import WeeklyAggregator

logger = logging.getLogger(__name__)


class TaskScheduler:
    """작업 스케줄러"""

    def __init__(
        self,
        naver_id: str = None,
        naver_pw: str = None,
        crawl_limit: int = 50
    ):
        self.naver_id = naver_id or os.getenv("NAVER_ID")
        self.naver_pw = naver_pw or os.getenv("NAVER_PW")
        self.crawl_limit = crawl_limit

        self.scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
        self._is_running = False

    def add_crawl_job(
        self,
        hour: int = 6,
        minute: int = 0,
        job_id: str = "daily_crawl"
    ):
        """데일리 크롤링 작업 추가"""
        self.scheduler.add_job(
            self._run_crawl,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name="Daily Crawling",
            replace_existing=True
        )
        logger.info(f"Added crawl job: {job_id} at {hour:02d}:{minute:02d}")

    def add_report_job(
        self,
        hour: int = 7,
        minute: int = 0,
        job_id: str = "daily_report"
    ):
        """데일리 리포트 생성 작업 추가"""
        self.scheduler.add_job(
            self._run_report_generation,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name="Daily Report Generation",
            replace_existing=True
        )
        logger.info(f"Added report job: {job_id} at {hour:02d}:{minute:02d}")

    def add_interval_crawl(
        self,
        hours: int = 4,
        job_id: str = "interval_crawl"
    ):
        """주기적 크롤링 작업 추가 (N시간마다)"""
        self.scheduler.add_job(
            self._run_crawl,
            IntervalTrigger(hours=hours),
            id=job_id,
            name=f"Interval Crawling (every {hours}h)",
            replace_existing=True
        )
        logger.info(f"Added interval crawl job: {job_id} every {hours} hours")

    def add_weekly_aggregation_job(
        self,
        day_of_week: str = "mon",
        hour: int = 2,
        minute: int = 0,
        job_id: str = "weekly_aggregation"
    ):
        """주간 집계 작업 추가 (매주 특정 요일)"""
        self.scheduler.add_job(
            self._run_weekly_aggregation,
            CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
            id=job_id,
            name="Weekly Aggregation",
            replace_existing=True
        )
        logger.info(f"Added weekly aggregation job: {job_id} on {day_of_week} at {hour:02d}:{minute:02d}")

    async def _run_crawl(self):
        """크롤링 작업 실행"""
        logger.info("Starting scheduled crawl")

        db = SessionLocal()
        try:
            orchestrator = CrawlerOrchestrator(
                db=db,
                naver_id=self.naver_id,
                naver_pw=self.naver_pw
            )
            results = await orchestrator.crawl_all_sources(limit=self.crawl_limit)

            success_count = sum(1 for r in results if r['success'])
            total_posts = sum(r['posts_collected'] for r in results)
            total_mentions = sum(r['mentions_found'] for r in results)

            logger.info(
                f"Crawl completed: {success_count}/{len(results)} sources, "
                f"{total_posts} posts, {total_mentions} mentions"
            )

        except Exception as e:
            logger.error(f"Crawl error: {e}")
        finally:
            db.close()

    async def _run_report_generation(self):
        """리포트 생성 작업 실행"""
        logger.info("Starting scheduled report generation")

        db = SessionLocal()
        try:
            generator = ReportGenerator(db)
            stats = generator.generate_all_reports()

            logger.info(
                f"Report generation completed: "
                f"{stats['teacher_reports']} teacher reports, "
                f"{stats['academy_stats']} academy stats"
            )

        except Exception as e:
            logger.error(f"Report generation error: {e}")
        finally:
            db.close()

    async def _run_weekly_aggregation(self):
        """주간 집계 작업 실행"""
        logger.info("Starting scheduled weekly aggregation")

        db = SessionLocal()
        try:
            aggregator = WeeklyAggregator(db)
            count = aggregator.aggregate_weekly_reports()

            logger.info(f"Weekly aggregation completed: {count} reports aggregated")

        except Exception as e:
            logger.error(f"Weekly aggregation error: {e}")
        finally:
            db.close()

    def setup_default_jobs(self):
        """기본 작업 설정"""
        # 매일 새벽 1시: 크롤링
        self.add_crawl_job(hour=1, minute=0)

        # 매일 새벽 1시 30분: 리포트 생성
        self.add_report_job(hour=1, minute=30)

        # 4시간마다: 추가 크롤링
        self.add_interval_crawl(hours=4)

        # 매주 월요일 새벽 2시: 주간 집계
        self.add_weekly_aggregation_job(day_of_week="mon", hour=2, minute=0)

        logger.info(
            "Default jobs configured: "
            "daily crawl 01:00, daily report 01:30, "
            "interval crawl 4h, weekly aggregation Mon 02:00"
        )

    def start(self):
        """스케줄러 시작"""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        self.scheduler.start()
        self._is_running = True
        logger.info("Scheduler started")

        jobs = self.scheduler.get_jobs()
        logger.info(f"Registered jobs: {len(jobs)}")
        for job in jobs:
            logger.info(f"  - {job.name}: next run at {job.next_run_time}")

    def stop(self):
        """스케줄러 중지"""
        if not self._is_running:
            logger.warning("Scheduler is not running")
            return

        self.scheduler.shutdown()
        self._is_running = False
        logger.info("Scheduler stopped")

    def run_now(self, job_type: str = "crawl"):
        """즉시 작업 실행"""
        if job_type == "crawl":
            asyncio.create_task(self._run_crawl())
        elif job_type == "report":
            asyncio.create_task(self._run_report_generation())
        elif job_type == "weekly":
            asyncio.create_task(self._run_weekly_aggregation())
        else:
            logger.warning(f"Unknown job type: {job_type}")

    def get_status(self) -> dict:
        """스케줄러 상태 조회"""
        jobs = self.scheduler.get_jobs()
        return {
            'is_running': self._is_running,
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': str(job.next_run_time) if job.next_run_time else None
                }
                for job in jobs
            ]
        }


async def run_scheduler():
    """스케줄러 실행 (메인 함수)"""
    scheduler = TaskScheduler()
    scheduler.setup_default_jobs()
    scheduler.start()

    logger.info("Scheduler running. Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(run_scheduler())
