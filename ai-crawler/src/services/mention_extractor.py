"""
Mention Extractor Service
게시글에서 강사 멘션 추출 및 저장
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)

from .teacher_matcher import TeacherMatcher, MatchResult
from .sentiment_analyzer import SentimentAnalyzer
from ..models import (
    Post, Comment, TeacherMention, Teacher, CollectionSource
)


class MentionExtractor:
    """강사 멘션 추출 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.matcher = TeacherMatcher(db)
        self.analyzer = SentimentAnalyzer(db)
        self._initialized = False

    def initialize(self):
        """서비스 초기화 (강사 정보 및 키워드 로드)"""
        if self._initialized:
            return

        self.matcher.load_teachers()
        self.analyzer.load_keywords()
        self._initialized = True

    def extract_and_save(self, post: Post) -> List[TeacherMention]:
        """
        게시글에서 멘션 추출 및 저장

        Args:
            post: Post 모델 객체

        Returns:
            생성된 TeacherMention 목록
        """
        self.initialize()

        mentions = []

        # 제목에서 멘션 찾기
        title_mentions = self.matcher.find_mentions(post.title or '')
        for match in title_mentions:
            mention = self._create_mention(
                post=post,
                match=match,
                mention_type='title',
                text=post.title
            )
            if mention:
                mentions.append(mention)

        # 본문에서 멘션 찾기
        content_mentions = self.matcher.find_mentions(post.content or '')
        for match in content_mentions:
            mention = self._create_mention(
                post=post,
                match=match,
                mention_type='content',
                text=post.content
            )
            if mention:
                mentions.append(mention)

        # 댓글에서 멘션 찾기
        if post.comments:
            for comment in post.comments:
                comment_mentions = self.matcher.find_mentions(comment.content or '')
                for match in comment_mentions:
                    mention = self._create_mention(
                        post=post,
                        comment=comment,
                        match=match,
                        mention_type='comment',
                        text=comment.content
                    )
                    if mention:
                        mentions.append(mention)

        return mentions

    def _create_mention(
        self,
        post: Post,
        match: MatchResult,
        mention_type: str,
        text: str,
        comment: Comment = None
    ) -> Optional[TeacherMention]:
        """멘션 생성 및 분석"""

        # 중복 체크
        existing = self.db.query(TeacherMention).filter(
            and_(
                TeacherMention.teacher_id == match.teacher_id,
                TeacherMention.post_id == post.id,
                TeacherMention.comment_id == (comment.id if comment else None),
                TeacherMention.mention_type == mention_type
            )
        ).first()

        if existing:
            return None

        # 감성/난이도 분석
        analysis = self.analyzer.analyze(text)

        mention = TeacherMention(
            teacher_id=match.teacher_id,
            post_id=post.id,
            comment_id=comment.id if comment else None,
            mention_type=mention_type,
            matched_text=match.matched_text,
            context=match.context,
            sentiment=analysis['sentiment'],
            sentiment_score=analysis['sentiment_score'],
            difficulty=analysis['difficulty'],
            is_recommended=analysis['is_recommended'],
            analyzed_at=datetime.utcnow()
        )

        self.db.add(mention)
        self.db.flush()

        return mention

    def process_crawled_data(
        self,
        source: CollectionSource,
        crawled_posts: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        크롤링된 데이터 처리

        Args:
            source: CollectionSource 모델
            crawled_posts: 크롤러에서 반환된 게시글 목록

        Returns:
            처리 통계 (posts_created, comments_created, mentions_found)
        """
        self.initialize()

        stats = {
            'posts_created': 0,
            'posts_updated': 0,
            'comments_created': 0,
            'mentions_found': 0
        }

        for post_data in crawled_posts:
            try:
                # 게시글 저장/업데이트
                post, created = self._save_post(source, post_data)
                if created:
                    stats['posts_created'] += 1
                else:
                    stats['posts_updated'] += 1

                # 댓글 저장
                comments_data = post_data.get('comments', [])
                for comment_data in comments_data:
                    comment, created = self._save_comment(post, comment_data)
                    if created:
                        stats['comments_created'] += 1

                # 멘션 추출
                mentions = self.extract_and_save(post)
                stats['mentions_found'] += len(mentions)

            except Exception as e:
                logger.error(f"Error processing post: {e}")
                self.db.rollback()
                continue

        # 전체 처리 완료 후 1회 commit (건별 commit 대신 배치 commit)
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Error committing batch: {e}")
            self.db.rollback()

        return stats

    def _save_post(self, source: CollectionSource, data: Dict[str, Any]) -> tuple:
        """게시글 저장"""
        external_id = data.get('external_id')

        existing = self.db.query(Post).filter(
            and_(
                Post.source_id == source.id,
                Post.external_id == external_id
            )
        ).first()

        if existing:
            # 업데이트
            existing.title = data.get('title', existing.title)
            existing.content = data.get('content', existing.content)
            existing.view_count = data.get('view_count', existing.view_count)
            existing.like_count = data.get('like_count', existing.like_count)
            existing.comment_count = data.get('comment_count', existing.comment_count)
            self.db.flush()
            return existing, False

        # 새로 생성
        post = Post(
            source_id=source.id,
            external_id=external_id,
            title=data.get('title', ''),
            content=data.get('content', ''),
            url=data.get('url', ''),
            author=data.get('author', ''),
            post_date=data.get('post_date'),
            view_count=data.get('view_count', 0),
            like_count=data.get('like_count', 0),
            comment_count=data.get('comment_count', 0)
        )

        self.db.add(post)
        self.db.flush()

        return post, True

    def _save_comment(self, post: Post, data: Dict[str, Any]) -> tuple:
        """댓글 저장"""
        external_id = data.get('external_id', '')

        # 간단한 중복 체크 (post_id + external_id)
        existing = self.db.query(Comment).filter(
            and_(
                Comment.post_id == post.id,
                Comment.external_id == external_id
            )
        ).first()

        if existing:
            return existing, False

        comment = Comment(
            post_id=post.id,
            external_id=external_id,
            content=data.get('content', ''),
            author=data.get('author', ''),
            comment_date=data.get('comment_date'),
            like_count=data.get('like_count', 0)
        )

        self.db.add(comment)
        self.db.flush()

        return comment, True

    def get_teacher_mentions_summary(self, teacher_id: int, days: int = 7) -> Dict[str, Any]:
        """강사별 멘션 요약"""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)

        mentions = self.db.query(TeacherMention).join(Post).filter(
            and_(
                TeacherMention.teacher_id == teacher_id,
                Post.post_date >= cutoff
            )
        ).all()

        summary = {
            'total_mentions': len(mentions),
            'title_mentions': len([m for m in mentions if m.mention_type == 'title']),
            'content_mentions': len([m for m in mentions if m.mention_type == 'content']),
            'comment_mentions': len([m for m in mentions if m.mention_type == 'comment']),
            'positive': len([m for m in mentions if m.sentiment == 'POSITIVE']),
            'negative': len([m for m in mentions if m.sentiment == 'NEGATIVE']),
            'neutral': len([m for m in mentions if m.sentiment == 'NEUTRAL']),
            'recommendations': len([m for m in mentions if m.is_recommended]),
            'difficulty_easy': len([m for m in mentions if m.difficulty == 'EASY']),
            'difficulty_medium': len([m for m in mentions if m.difficulty == 'MEDIUM']),
            'difficulty_hard': len([m for m in mentions if m.difficulty == 'HARD']),
        }

        # 평균 감성 점수
        scores = [m.sentiment_score for m in mentions if m.sentiment_score is not None]
        summary['avg_sentiment_score'] = sum(scores) / len(scores) if scores else None

        return summary
