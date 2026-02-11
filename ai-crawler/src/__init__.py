"""
TeacherHub AI Crawler Package
"""
from .database import engine, SessionLocal, get_db, get_session, init_db, Base
from .models import (
    Academy, Subject, Teacher, CollectionSource, Post, Comment,
    TeacherMention, DailyReport, AcademyDailyStats, CrawlLog,
    AnalysisKeyword, ReputationData
)
from .repositories import (
    AcademyRepository, SubjectRepository, TeacherRepository,
    CollectionSourceRepository, PostRepository, CommentRepository,
    TeacherMentionRepository, DailyReportRepository,
    AcademyDailyStatsRepository, CrawlLogRepository, AnalysisKeywordRepository
)
from .crawlers import BaseCrawler, NaverCafeCrawler, DCInsideCrawler
from .services import TeacherMatcher, MentionExtractor, SentimentAnalyzer, ReportGenerator, WeeklyAggregator
from .orchestrator import CrawlerOrchestrator, run_daily_crawl
from .scheduler import TaskScheduler, run_scheduler

__all__ = [
    # Database
    'engine', 'SessionLocal', 'get_db', 'get_session', 'init_db', 'Base',
    # Models
    'Academy', 'Subject', 'Teacher', 'CollectionSource', 'Post', 'Comment',
    'TeacherMention', 'DailyReport', 'AcademyDailyStats', 'CrawlLog',
    'AnalysisKeyword', 'ReputationData',
    # Repositories
    'AcademyRepository', 'SubjectRepository', 'TeacherRepository',
    'CollectionSourceRepository', 'PostRepository', 'CommentRepository',
    'TeacherMentionRepository', 'DailyReportRepository',
    'AcademyDailyStatsRepository', 'CrawlLogRepository', 'AnalysisKeywordRepository',
    # Crawlers
    'BaseCrawler', 'NaverCafeCrawler', 'DCInsideCrawler',
    # Services
    'TeacherMatcher', 'MentionExtractor', 'SentimentAnalyzer', 'ReportGenerator', 'WeeklyAggregator',
    # Orchestrator & Scheduler
    'CrawlerOrchestrator', 'run_daily_crawl',
    'TaskScheduler', 'run_scheduler',
]
