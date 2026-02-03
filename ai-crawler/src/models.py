"""
TeacherHub V2 SQLAlchemy Models
강사 평판 분석 시스템
"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, Date,
    ForeignKey, UniqueConstraint, Index, ARRAY
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .database import Base


# ============================================
# 1. 학원 테이블
# ============================================
class Academy(Base):
    """공무원 학원 정보"""
    __tablename__ = 'academies'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)  # gongdangi, hackers, willbes, eduwill
    website = Column(String(200))
    logo_url = Column(String(300))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teachers = relationship("Teacher", back_populates="academy")
    daily_stats = relationship("AcademyDailyStats", back_populates="academy")


# ============================================
# 2. 과목 테이블
# ============================================
class Subject(Base):
    """시험 과목 정보"""
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=False)  # common, major, psat
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teachers = relationship("Teacher", back_populates="subject")


# ============================================
# 3. 강사 테이블
# ============================================
class Teacher(Base):
    """강사 정보"""
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True)
    academy_id = Column(Integer, ForeignKey('academies.id', ondelete='SET NULL'))
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='SET NULL'))
    name = Column(String(100), nullable=False)
    aliases = Column(ARRAY(Text))  # 별명, 이름 변형 배열
    profile_url = Column(String(300))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    academy = relationship("Academy", back_populates="teachers")
    subject = relationship("Subject", back_populates="teachers")
    mentions = relationship("TeacherMention", back_populates="teacher")
    daily_reports = relationship("DailyReport", back_populates="teacher")

    # Indexes
    __table_args__ = (
        Index('idx_teachers_academy', 'academy_id'),
        Index('idx_teachers_subject', 'subject_id'),
        Index('idx_teachers_name', 'name'),
    )

    def get_all_names(self) -> List[str]:
        """강사 이름과 모든 별명 반환"""
        names = [self.name]
        if self.aliases:
            names.extend(self.aliases)
        return names


# ============================================
# 4. 수집 소스 테이블
# ============================================
class CollectionSource(Base):
    """데이터 수집 소스 정보"""
    __tablename__ = 'collection_sources'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)  # naver_cafe, dcinside, fmkorea
    base_url = Column(String(300))
    source_type = Column(String(50))  # cafe, gallery, forum
    is_active = Column(Boolean, default=True)
    config = Column(JSONB)  # 크롤링 설정 (로그인 필요 여부 등)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="source")
    crawl_logs = relationship("CrawlLog", back_populates="source")


# ============================================
# 5. 게시글 테이블
# ============================================
class Post(Base):
    """수집된 게시글"""
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('collection_sources.id'))
    external_id = Column(String(100))  # 원본 게시글 ID
    title = Column(String(500), nullable=False)
    content = Column(Text)
    url = Column(String(500))
    author = Column(String(100))
    post_date = Column(DateTime)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    collected_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source = relationship("CollectionSource", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    mentions = relationship("TeacherMention", back_populates="post", cascade="all, delete-orphan")

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint('source_id', 'external_id', name='uq_posts_source_external'),
        Index('idx_posts_source', 'source_id'),
        Index('idx_posts_date', 'post_date'),
        Index('idx_posts_collected', 'collected_at'),
    )


# ============================================
# 6. 댓글 테이블
# ============================================
class Comment(Base):
    """게시글 댓글"""
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'))
    external_id = Column(String(100))
    content = Column(Text)
    author = Column(String(100))
    comment_date = Column(DateTime)
    like_count = Column(Integer, default=0)
    collected_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="comments")
    mentions = relationship("TeacherMention", back_populates="comment", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_comments_post', 'post_id'),
    )


# ============================================
# 7. 강사 멘션 테이블
# ============================================
class TeacherMention(Base):
    """강사 멘션 및 분석 결과"""
    __tablename__ = 'teacher_mentions'

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='CASCADE'))
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'))
    comment_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=True)

    mention_type = Column(String(20), nullable=False)  # title, content, comment
    matched_text = Column(String(200))  # 매칭된 텍스트
    context = Column(Text)  # 주변 문맥 (앞뒤 100자)

    # 분석 결과
    sentiment = Column(String(20))  # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score = Column(Float)  # -1.0 ~ 1.0
    difficulty = Column(String(20))  # EASY, MEDIUM, HARD
    is_recommended = Column(Boolean)

    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teacher = relationship("Teacher", back_populates="mentions")
    post = relationship("Post", back_populates="mentions")
    comment = relationship("Comment", back_populates="mentions")

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint('teacher_id', 'post_id', 'comment_id', 'mention_type',
                        name='uq_mentions_teacher_post_comment_type'),
        Index('idx_mentions_teacher', 'teacher_id'),
        Index('idx_mentions_post', 'post_id'),
        Index('idx_mentions_analyzed', 'analyzed_at'),
    )


# ============================================
# 8. 데일리 리포트 테이블
# ============================================
class DailyReport(Base):
    """강사별 데일리 리포트"""
    __tablename__ = 'daily_reports'

    id = Column(Integer, primary_key=True)
    report_date = Column(Date, nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='CASCADE'))

    # 집계 데이터
    mention_count = Column(Integer, default=0)
    post_mention_count = Column(Integer, default=0)
    comment_mention_count = Column(Integer, default=0)

    # 감성 분석 집계
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    avg_sentiment_score = Column(Float)

    # 난이도 집계
    difficulty_easy_count = Column(Integer, default=0)
    difficulty_medium_count = Column(Integer, default=0)
    difficulty_hard_count = Column(Integer, default=0)

    # 추천 집계
    recommendation_count = Column(Integer, default=0)

    # 전일 대비 변화
    mention_change = Column(Integer, default=0)  # 전일 대비 증감
    sentiment_change = Column(Float)  # 전일 대비 감성 변화

    # AI 요약
    summary = Column(Text)
    top_keywords = Column(ARRAY(Text))  # 자주 언급된 키워드

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teacher = relationship("Teacher", back_populates="daily_reports")

    # Constraints & Indexes
    __table_args__ = (
        UniqueConstraint('report_date', 'teacher_id', name='uq_reports_date_teacher'),
        Index('idx_reports_date', 'report_date'),
        Index('idx_reports_teacher', 'teacher_id'),
    )


# ============================================
# 9. 학원별 데일리 집계 테이블
# ============================================
class AcademyDailyStats(Base):
    """학원별 데일리 통계"""
    __tablename__ = 'academy_daily_stats'

    id = Column(Integer, primary_key=True)
    report_date = Column(Date, nullable=False)
    academy_id = Column(Integer, ForeignKey('academies.id', ondelete='CASCADE'))

    total_mentions = Column(Integer, default=0)
    total_teachers_mentioned = Column(Integer, default=0)
    avg_sentiment_score = Column(Float)
    top_teacher_id = Column(Integer, ForeignKey('teachers.id'))

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    academy = relationship("Academy", back_populates="daily_stats")
    top_teacher = relationship("Teacher", foreign_keys=[top_teacher_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint('report_date', 'academy_id', name='uq_academy_stats_date_academy'),
    )


# ============================================
# 10. 크롤링 작업 로그 테이블
# ============================================
class CrawlLog(Base):
    """크롤링 작업 로그"""
    __tablename__ = 'crawl_logs'

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('collection_sources.id'))
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    status = Column(String(20), nullable=False)  # running, completed, failed
    posts_collected = Column(Integer, default=0)
    comments_collected = Column(Integer, default=0)
    mentions_found = Column(Integer, default=0)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source = relationship("CollectionSource", back_populates="crawl_logs")


# ============================================
# 11. 분석 키워드 사전 테이블
# ============================================
class AnalysisKeyword(Base):
    """분석용 키워드 사전"""
    __tablename__ = 'analysis_keywords'

    id = Column(Integer, primary_key=True)
    category = Column(String(50), nullable=False)  # sentiment_positive, sentiment_negative, difficulty_easy, etc.
    keyword = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint('category', 'keyword', name='uq_keywords_category_keyword'),
    )


# ============================================
# Legacy 테이블 (기존 호환성 유지)
# ============================================
class ReputationData(Base):
    """기존 reputation_data 테이블 (호환성 유지)"""
    __tablename__ = 'reputation_data'

    id = Column(Integer, primary_key=True)
    keyword = Column(String(100), nullable=False)
    site_name = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)
    sentiment = Column(String(20))
    score = Column(Float)
    post_date = Column(DateTime)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
