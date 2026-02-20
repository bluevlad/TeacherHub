"""
TeacherHub Repositories
데이터베이스 CRUD 작업 레이어
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from .models import (
    Academy, Subject, Teacher, CollectionSource, Post, Comment,
    TeacherMention, DailyReport, AcademyDailyStats, CrawlLog, AnalysisKeyword
)


class AcademyRepository:
    """학원 Repository"""

    @staticmethod
    def get_all(db: Session, active_only: bool = True) -> List[Academy]:
        query = db.query(Academy)
        if active_only:
            query = query.filter(Academy.is_active == True)
        return query.all()

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[Academy]:
        return db.query(Academy).filter(Academy.code == code).first()

    @staticmethod
    def get_by_id(db: Session, academy_id: int) -> Optional[Academy]:
        return db.query(Academy).filter(Academy.id == academy_id).first()


class SubjectRepository:
    """과목 Repository"""

    @staticmethod
    def get_all(db: Session) -> List[Subject]:
        return db.query(Subject).order_by(Subject.display_order).all()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Subject]:
        return db.query(Subject).filter(Subject.name == name).first()

    @staticmethod
    def get_by_category(db: Session, category: str) -> List[Subject]:
        return db.query(Subject).filter(Subject.category == category).all()


class TeacherRepository:
    """강사 Repository"""

    @staticmethod
    def get_all(db: Session, active_only: bool = True) -> List[Teacher]:
        query = db.query(Teacher)
        if active_only:
            query = query.filter(Teacher.is_active == True)
        return query.all()

    @staticmethod
    def get_by_academy(db: Session, academy_id: int, active_only: bool = True) -> List[Teacher]:
        query = db.query(Teacher).filter(Teacher.academy_id == academy_id)
        if active_only:
            query = query.filter(Teacher.is_active == True)
        return query.all()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Teacher]:
        return db.query(Teacher).filter(Teacher.name == name).first()

    @staticmethod
    def search_by_name_or_alias(db: Session, search_term: str) -> List[Teacher]:
        """이름 또는 별명으로 강사 검색"""
        return db.query(Teacher).filter(
            or_(
                Teacher.name.ilike(f'%{search_term}%'),
                Teacher.aliases.any(search_term)
            )
        ).all()

    @staticmethod
    def get_all_names_map(db: Session) -> Dict[str, int]:
        """모든 강사의 이름/별명 -> teacher_id 매핑 반환"""
        teachers = db.query(Teacher).filter(Teacher.is_active == True).all()
        name_map = {}
        for teacher in teachers:
            name_map[teacher.name] = teacher.id
            if teacher.aliases:
                for alias in teacher.aliases:
                    name_map[alias] = teacher.id
        return name_map


class CollectionSourceRepository:
    """수집 소스 Repository"""

    @staticmethod
    def get_all(db: Session, active_only: bool = True) -> List[CollectionSource]:
        query = db.query(CollectionSource)
        if active_only:
            query = query.filter(CollectionSource.is_active == True)
        return query.all()

    @staticmethod
    def get_by_code(db: Session, code: str) -> Optional[CollectionSource]:
        return db.query(CollectionSource).filter(CollectionSource.code == code).first()


class PostRepository:
    """게시글 Repository"""

    @staticmethod
    def create(db: Session, post_data: Dict[str, Any]) -> Post:
        post = Post(**post_data)
        db.add(post)
        db.flush()
        return post

    @staticmethod
    def get_or_create(db: Session, source_id: int, external_id: str, post_data: Dict[str, Any]) -> tuple[Post, bool]:
        """기존 게시글 조회 또는 새로 생성"""
        existing = db.query(Post).filter(
            and_(Post.source_id == source_id, Post.external_id == external_id)
        ).first()
        if existing:
            return existing, False
        post = Post(source_id=source_id, external_id=external_id, **post_data)
        db.add(post)
        db.flush()
        return post, True

    @staticmethod
    def get_by_date_range(db: Session, start_date: datetime, end_date: datetime,
                          source_id: Optional[int] = None) -> List[Post]:
        query = db.query(Post).filter(
            and_(Post.post_date >= start_date, Post.post_date <= end_date)
        )
        if source_id:
            query = query.filter(Post.source_id == source_id)
        return query.order_by(Post.post_date.desc()).all()


class CommentRepository:
    """댓글 Repository"""

    @staticmethod
    def create(db: Session, comment_data: Dict[str, Any]) -> Comment:
        comment = Comment(**comment_data)
        db.add(comment)
        db.flush()
        return comment

    @staticmethod
    def get_by_post(db: Session, post_id: int) -> List[Comment]:
        return db.query(Comment).filter(Comment.post_id == post_id).all()


class TeacherMentionRepository:
    """강사 멘션 Repository"""

    @staticmethod
    def create(db: Session, mention_data: Dict[str, Any]) -> TeacherMention:
        mention = TeacherMention(**mention_data)
        db.add(mention)
        db.flush()
        return mention

    @staticmethod
    def get_by_teacher_and_date(db: Session, teacher_id: int, start_date: datetime,
                                 end_date: datetime) -> List[TeacherMention]:
        return db.query(TeacherMention).join(Post).filter(
            and_(
                TeacherMention.teacher_id == teacher_id,
                Post.post_date >= start_date,
                Post.post_date <= end_date
            )
        ).all()

    @staticmethod
    def get_daily_stats(db: Session, teacher_id: int, report_date: date) -> Dict[str, Any]:
        """특정 날짜의 강사 통계 집계"""
        start = datetime.combine(report_date, datetime.min.time())
        end = datetime.combine(report_date, datetime.max.time())

        mentions = db.query(TeacherMention).join(Post).filter(
            and_(
                TeacherMention.teacher_id == teacher_id,
                Post.post_date >= start,
                Post.post_date <= end
            )
        ).all()

        stats = {
            'mention_count': len(mentions),
            'post_mention_count': len([m for m in mentions if m.mention_type in ('title', 'content')]),
            'comment_mention_count': len([m for m in mentions if m.mention_type == 'comment']),
            'positive_count': len([m for m in mentions if m.sentiment == 'POSITIVE']),
            'negative_count': len([m for m in mentions if m.sentiment == 'NEGATIVE']),
            'neutral_count': len([m for m in mentions if m.sentiment == 'NEUTRAL']),
            'difficulty_easy_count': len([m for m in mentions if m.difficulty == 'EASY']),
            'difficulty_medium_count': len([m for m in mentions if m.difficulty == 'MEDIUM']),
            'difficulty_hard_count': len([m for m in mentions if m.difficulty == 'HARD']),
            'recommendation_count': len([m for m in mentions if m.is_recommended]),
        }

        # 평균 감성 점수
        scores = [m.sentiment_score for m in mentions if m.sentiment_score is not None]
        stats['avg_sentiment_score'] = sum(scores) / len(scores) if scores else None

        return stats


class DailyReportRepository:
    """데일리 리포트 Repository"""

    @staticmethod
    def create_or_update(db: Session, report_date: date, teacher_id: int,
                         report_data: Dict[str, Any]) -> DailyReport:
        existing = db.query(DailyReport).filter(
            and_(DailyReport.report_date == report_date, DailyReport.teacher_id == teacher_id)
        ).first()

        if existing:
            for key, value in report_data.items():
                setattr(existing, key, value)
            db.flush()
            return existing

        report = DailyReport(report_date=report_date, teacher_id=teacher_id, **report_data)
        db.add(report)
        db.flush()
        return report

    @staticmethod
    def get_by_date(db: Session, report_date: date) -> List[DailyReport]:
        return db.query(DailyReport).filter(DailyReport.report_date == report_date).all()

    @staticmethod
    def get_teacher_history(db: Session, teacher_id: int, days: int = 30) -> List[DailyReport]:
        start_date = date.today() - timedelta(days=days)
        return db.query(DailyReport).filter(
            and_(
                DailyReport.teacher_id == teacher_id,
                DailyReport.report_date >= start_date
            )
        ).order_by(DailyReport.report_date.desc()).all()

    @staticmethod
    def get_previous_day_stats(db: Session, teacher_id: int, report_date: date) -> Optional[DailyReport]:
        prev_date = report_date - timedelta(days=1)
        return db.query(DailyReport).filter(
            and_(DailyReport.report_date == prev_date, DailyReport.teacher_id == teacher_id)
        ).first()


class AcademyDailyStatsRepository:
    """학원별 데일리 통계 Repository"""

    @staticmethod
    def create_or_update(db: Session, report_date: date, academy_id: int,
                         stats_data: Dict[str, Any]) -> AcademyDailyStats:
        existing = db.query(AcademyDailyStats).filter(
            and_(AcademyDailyStats.report_date == report_date,
                 AcademyDailyStats.academy_id == academy_id)
        ).first()

        if existing:
            for key, value in stats_data.items():
                setattr(existing, key, value)
            db.flush()
            return existing

        stats = AcademyDailyStats(report_date=report_date, academy_id=academy_id, **stats_data)
        db.add(stats)
        db.flush()
        return stats


class CrawlLogRepository:
    """크롤링 로그 Repository"""

    @staticmethod
    def start_crawl(db: Session, source_id: int) -> CrawlLog:
        log = CrawlLog(
            source_id=source_id,
            started_at=datetime.utcnow(),
            status='running'
        )
        db.add(log)
        db.flush()
        return log

    @staticmethod
    def finish_crawl(db: Session, log_id: int, posts: int, comments: int,
                     mentions: int, error: Optional[str] = None) -> CrawlLog:
        log = db.query(CrawlLog).filter(CrawlLog.id == log_id).first()
        if log:
            log.finished_at = datetime.utcnow()
            log.status = 'failed' if error else 'completed'
            log.posts_collected = posts
            log.comments_collected = comments
            log.mentions_found = mentions
            log.error_message = error
            db.flush()
        return log

    @staticmethod
    def get_recent_logs(db: Session, source_id: Optional[int] = None, limit: int = 10) -> List[CrawlLog]:
        query = db.query(CrawlLog)
        if source_id:
            query = query.filter(CrawlLog.source_id == source_id)
        return query.order_by(CrawlLog.created_at.desc()).limit(limit).all()


class AnalysisKeywordRepository:
    """분석 키워드 Repository"""

    @staticmethod
    def get_by_category(db: Session, category: str, active_only: bool = True) -> List[AnalysisKeyword]:
        query = db.query(AnalysisKeyword).filter(AnalysisKeyword.category == category)
        if active_only:
            query = query.filter(AnalysisKeyword.is_active == True)
        return query.all()

    @staticmethod
    def get_all_keywords_map(db: Session) -> Dict[str, List[Dict[str, Any]]]:
        """카테고리별 키워드 맵 반환"""
        keywords = db.query(AnalysisKeyword).filter(AnalysisKeyword.is_active == True).all()
        result = {}
        for kw in keywords:
            if kw.category not in result:
                result[kw.category] = []
            result[kw.category].append({
                'keyword': kw.keyword,
                'weight': kw.weight
            })
        return result
