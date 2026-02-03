"""
Task Scheduler
자동화된 크롤링 및 리포트 생성 스케줄러
"""
import asyncio
import os
from datetime import datetime, time, timedelta
from typing import Callable, Optional
import threading
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .database import SessionLocal
from .orchestrator import CrawlerOrchestrator
from .services.report_generator import ReportGenerator
from .services.weekly_aggregator import WeeklyAggregator


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
        """
        데일리 크롤링 작업 추가

        Args:
            hour: 실행 시간 (시)
            minute: 실행 시간 (분)
            job_id: 작업 ID
        """
        self.scheduler.add_job(
            self._run_crawl,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name="Daily Crawling",
            replace_existing=True
        )
        print(f"[+] Added crawl job: {job_id} at {hour:02d}:{minute:02d}")

    def add_report_job(
        self,
        hour: int = 7,
        minute: int = 0,
        job_id: str = "daily_report"
    ):
        """
        데일리 리포트 생성 작업 추가

        Args:
            hour: 실행 시간 (시)
            minute: 실행 시간 (분)
            job_id: 작업 ID
        """
        self.scheduler.add_job(
            self._run_report_generation,
            CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name="Daily Report Generation",
            replace_existing=True
        )
        print(f"[+] Added report job: {job_id} at {hour:02d}:{minute:02d}")

    def add_interval_crawl(
        self,
        hours: int = 4,
        job_id: str = "interval_crawl"
    ):
        """
        주기적 크롤링 작업 추가 (N시간마다)

        Args:
            hours: 실행 주기 (시간)
            job_id: 작업 ID
        """
        self.scheduler.add_job(
            self._run_crawl,
            IntervalTrigger(hours=hours),
            id=job_id,
            name=f"Interval Crawling (every {hours}h)",
            replace_existing=True
        )
        print(f"[+] Added interval crawl job: {job_id} every {hours} hours")

    def add_weekly_aggregation_job(
        self,
        day_of_week: str = "mon",
        hour: int = 2,
        minute: int = 0,
        job_id: str = "weekly_aggregation"
    ):
        """
        주간 집계 작업 추가 (매주 특정 요일)

        Args:
            day_of_week: 실행 요일 (mon, tue, wed, thu, fri, sat, sun)
            hour: 실행 시간 (시)
            minute: 실행 시간 (분)
            job_id: 작업 ID
        """
        self.scheduler.add_job(
            self._run_weekly_aggregation,
            CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
            id=job_id,
            name="Weekly Aggregation",
            replace_existing=True
        )
        print(f"[+] Added weekly aggregation job: {job_id} on {day_of_week} at {hour:02d}:{minute:02d}")

    async def _run_crawl(self):
        """크롤링 작업 실행"""
        print(f"\n{'='*50}")
        print(f"[{datetime.now()}] Starting scheduled crawl")
        print(f"{'='*50}")

        db = SessionLocal()
        try:
            orchestrator = CrawlerOrchestrator(
                db=db,
                naver_id=self.naver_id,
                naver_pw=self.naver_pw
            )
            results = await orchestrator.crawl_all_sources(limit=self.crawl_limit)

            # 결과 로깅
            success_count = sum(1 for r in results if r['success'])
            total_posts = sum(r['posts_collected'] for r in results)
            total_mentions = sum(r['mentions_found'] for r in results)

            print(f"\n[{datetime.now()}] Crawl completed")
            print(f"  Sources: {success_count}/{len(results)} successful")
            print(f"  Posts: {total_posts}")
            print(f"  Mentions: {total_mentions}")

        except Exception as e:
            print(f"[!] Crawl error: {e}")
        finally:
            db.close()

    async def _run_report_generation(self):
        """리포트 생성 작업 실행"""
        print(f"\n{'='*50}")
        print(f"[{datetime.now()}] Starting scheduled report generation")
        print(f"{'='*50}")

        db = SessionLocal()
        try:
            generator = ReportGenerator(db)
            stats = generator.generate_all_reports()

            print(f"\n[{datetime.now()}] Report generation completed")
            print(f"  Teacher reports: {stats['teacher_reports']}")
            print(f"  Academy stats: {stats['academy_stats']}")

        except Exception as e:
            print(f"[!] Report generation error: {e}")
        finally:
            db.close()

    async def _run_weekly_aggregation(self):
        """주간 집계 작업 실행"""
        print(f"\n{'='*50}")
        print(f"[{datetime.now()}] Starting scheduled weekly aggregation")
        print(f"{'='*50}")

        db = SessionLocal()
        try:
            aggregator = WeeklyAggregator(db)
            count = aggregator.aggregate_weekly_reports()

            print(f"\n[{datetime.now()}] Weekly aggregation completed")
            print(f"  Reports aggregated: {count}")

        except Exception as e:
            print(f"[!] Weekly aggregation error: {e}")
        finally:
            db.close()

    def setup_default_jobs(self):
        """기본 작업 설정"""
        # 매일 오전 6시: 크롤링
        self.add_crawl_job(hour=6, minute=0)

        # 매일 오전 7시: 리포트 생성
        self.add_report_job(hour=7, minute=0)

        # 4시간마다: 추가 크롤링
        self.add_interval_crawl(hours=4)

        # 매주 월요일 새벽 2시: 주간 집계
        self.add_weekly_aggregation_job(day_of_week="mon", hour=2, minute=0)

        print("\n[*] Default jobs configured:")
        print("    - Daily crawl at 06:00")
        print("    - Daily report at 07:00")
        print("    - Interval crawl every 4 hours")
        print("    - Weekly aggregation on Monday at 02:00")

    def start(self):
        """스케줄러 시작"""
        if self._is_running:
            print("[!] Scheduler is already running")
            return

        self.scheduler.start()
        self._is_running = True
        print("\n[*] Scheduler started")

        # 등록된 작업 출력
        jobs = self.scheduler.get_jobs()
        print(f"[*] Registered jobs: {len(jobs)}")
        for job in jobs:
            print(f"    - {job.name}: {job.next_run_time}")

    def stop(self):
        """스케줄러 중지"""
        if not self._is_running:
            print("[!] Scheduler is not running")
            return

        self.scheduler.shutdown()
        self._is_running = False
        print("[*] Scheduler stopped")

    def run_now(self, job_type: str = "crawl"):
        """
        즉시 작업 실행

        Args:
            job_type: 'crawl', 'report', 또는 'weekly'
        """
        if job_type == "crawl":
            asyncio.create_task(self._run_crawl())
        elif job_type == "report":
            asyncio.create_task(self._run_report_generation())
        elif job_type == "weekly":
            asyncio.create_task(self._run_weekly_aggregation())
        else:
            print(f"[!] Unknown job type: {job_type}")

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

    print("\n[*] Press Ctrl+C to stop")

    try:
        # 무한 대기
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(run_scheduler())
