"""
TeacherHub CLI
명령줄 인터페이스
"""
import asyncio
import argparse
import os
from datetime import date, datetime, timedelta

from .database import SessionLocal, init_db
from .orchestrator import CrawlerOrchestrator
from .services.report_generator import ReportGenerator
from .scheduler import TaskScheduler


def cmd_crawl(args):
    """크롤링 명령 실행"""
    print(f"\n{'='*50}")
    print("TeacherHub Crawler")
    print(f"{'='*50}")

    db = SessionLocal()
    try:
        orchestrator = CrawlerOrchestrator(
            db=db,
            naver_id=args.naver_id or os.getenv("NAVER_ID"),
            naver_pw=args.naver_pw or os.getenv("NAVER_PW")
        )

        if args.source:
            # 특정 소스만 크롤링
            from .models import CollectionSource
            source = db.query(CollectionSource).filter(
                CollectionSource.code == args.source
            ).first()

            if not source:
                print(f"[!] Unknown source: {args.source}")
                return

            result = asyncio.run(orchestrator.crawl_source(
                source,
                keyword=args.keyword,
                limit=args.limit
            ))
            print(f"\nResult: {result}")
        else:
            # 전체 소스 크롤링
            results = asyncio.run(orchestrator.crawl_all_sources(
                keyword=args.keyword,
                limit=args.limit
            ))

    finally:
        db.close()


def cmd_report(args):
    """리포트 생성 명령 실행"""
    print(f"\n{'='*50}")
    print("TeacherHub Report Generator")
    print(f"{'='*50}")

    # 날짜 파싱
    if args.date:
        try:
            report_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"[!] Invalid date format: {args.date} (use YYYY-MM-DD)")
            return
    else:
        report_date = date.today()

    db = SessionLocal()
    try:
        generator = ReportGenerator(db)

        if args.teacher_id:
            # 특정 강사만
            report = generator.generate_teacher_report(args.teacher_id, report_date)
            if report:
                print(f"\nReport for teacher {args.teacher_id}:")
                print(f"  Date: {report.report_date}")
                print(f"  Mentions: {report.mention_count}")
                print(f"  Positive: {report.positive_count}")
                print(f"  Negative: {report.negative_count}")
                print(f"  Avg Sentiment: {report.avg_sentiment_score}")
                print(f"  Summary: {report.summary}")
            else:
                print(f"[!] No data for teacher {args.teacher_id}")
        else:
            # 전체 리포트
            stats = generator.generate_all_reports(report_date)
            print(f"\nGenerated {stats['teacher_reports']} teacher reports")
            print(f"Generated {stats['academy_stats']} academy stats")

            # 요약 출력
            if args.summary:
                summary = generator.get_report_summary(report_date)
                print(f"\n{'='*50}")
                print("Daily Summary")
                print(f"{'='*50}")
                print(f"Total Mentions: {summary['total_mentions']}")
                print(f"Positive Ratio: {summary['positive_ratio']:.1f}%")
                print(f"Top Mentioned Teachers:")
                for t in summary['top_mentioned_teachers'][:5]:
                    print(f"  - ID {t['teacher_id']}: {t['mention_count']} mentions")

    finally:
        db.close()


def cmd_status(args):
    """상태 확인 명령"""
    print(f"\n{'='*50}")
    print("TeacherHub Status")
    print(f"{'='*50}")

    db = SessionLocal()
    try:
        from .models import (
            Teacher, Academy, CollectionSource, Post, TeacherMention,
            DailyReport, CrawlLog
        )

        # 기본 통계
        print("\n[Database Statistics]")
        print(f"  Academies: {db.query(Academy).count()}")
        print(f"  Teachers: {db.query(Teacher).filter(Teacher.is_active == True).count()}")
        print(f"  Sources: {db.query(CollectionSource).filter(CollectionSource.is_active == True).count()}")
        print(f"  Posts: {db.query(Post).count()}")
        print(f"  Mentions: {db.query(TeacherMention).count()}")
        print(f"  Daily Reports: {db.query(DailyReport).count()}")

        # 최근 크롤링 로그
        recent_logs = db.query(CrawlLog).order_by(
            CrawlLog.created_at.desc()
        ).limit(5).all()

        if recent_logs:
            print("\n[Recent Crawl Logs]")
            for log in recent_logs:
                status_icon = "✓" if log.status == "completed" else "✗" if log.status == "failed" else "⋯"
                print(f"  {status_icon} {log.started_at}: {log.posts_collected} posts, {log.mentions_found} mentions")

        # 오늘 리포트 요약
        today = date.today()
        today_reports = db.query(DailyReport).filter(
            DailyReport.report_date == today
        ).count()

        print(f"\n[Today's Reports]")
        print(f"  Reports generated: {today_reports}")

    finally:
        db.close()


def cmd_scheduler(args):
    """스케줄러 명령"""
    if args.action == "start":
        print("[*] Starting scheduler...")
        asyncio.run(run_scheduler_async())
    elif args.action == "status":
        scheduler = TaskScheduler()
        status = scheduler.get_status()
        print(f"Scheduler running: {status['is_running']}")
        print(f"Jobs: {len(status['jobs'])}")
        for job in status['jobs']:
            print(f"  - {job['name']}: next run at {job['next_run']}")
    else:
        print(f"[!] Unknown action: {args.action}")


async def run_scheduler_async():
    """비동기 스케줄러 실행"""
    from .scheduler import run_scheduler
    await run_scheduler()


def cmd_init_db(args):
    """데이터베이스 초기화"""
    print("[*] Initializing database...")
    init_db()
    print("[+] Database initialized")


def main():
    """메인 CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(
        description="TeacherHub AI Crawler CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # crawl 명령
    crawl_parser = subparsers.add_parser("crawl", help="Run crawler")
    crawl_parser.add_argument("-s", "--source", help="Source code to crawl")
    crawl_parser.add_argument("-k", "--keyword", help="Search keyword")
    crawl_parser.add_argument("-l", "--limit", type=int, default=50, help="Max posts to crawl")
    crawl_parser.add_argument("--naver-id", help="Naver ID for login")
    crawl_parser.add_argument("--naver-pw", help="Naver password for login")

    # report 명령
    report_parser = subparsers.add_parser("report", help="Generate reports")
    report_parser.add_argument("-d", "--date", help="Report date (YYYY-MM-DD)")
    report_parser.add_argument("-t", "--teacher-id", type=int, help="Teacher ID")
    report_parser.add_argument("--summary", action="store_true", help="Show summary")

    # status 명령
    status_parser = subparsers.add_parser("status", help="Show status")

    # scheduler 명령
    scheduler_parser = subparsers.add_parser("scheduler", help="Scheduler control")
    scheduler_parser.add_argument("action", choices=["start", "status"], help="Action")

    # init-db 명령
    init_parser = subparsers.add_parser("init-db", help="Initialize database")

    args = parser.parse_args()

    if args.command == "crawl":
        cmd_crawl(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "scheduler":
        cmd_scheduler(args)
    elif args.command == "init-db":
        cmd_init_db(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
