"""
Daily Report Generator Service
데일리 리포트 생성 서비스
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models import (
    Teacher, Academy, TeacherMention, DailyReport,
    AcademyDailyStats, Post, Comment
)


class ReportGenerator:
    """데일리 리포트 생성 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def generate_teacher_report(
        self,
        teacher_id: int,
        report_date: date = None
    ) -> Optional[DailyReport]:
        """
        강사별 데일리 리포트 생성

        Args:
            teacher_id: 강사 ID
            report_date: 리포트 날짜 (기본: 오늘)

        Returns:
            생성된 DailyReport
        """
        if report_date is None:
            report_date = date.today()

        # 해당 날짜의 멘션 조회
        start_dt = datetime.combine(report_date, datetime.min.time())
        end_dt = datetime.combine(report_date, datetime.max.time())

        mentions = self.db.query(TeacherMention).join(Post).filter(
            and_(
                TeacherMention.teacher_id == teacher_id,
                Post.post_date >= start_dt,
                Post.post_date <= end_dt
            )
        ).all()

        if not mentions:
            return None

        # 통계 계산
        stats = self._calculate_stats(mentions)

        # 전일 대비 변화 계산
        prev_report = self._get_previous_report(teacher_id, report_date)
        mention_change = 0
        sentiment_change = None

        if prev_report:
            mention_change = stats['mention_count'] - (prev_report.mention_count or 0)
            if prev_report.avg_sentiment_score is not None and stats['avg_sentiment_score'] is not None:
                sentiment_change = stats['avg_sentiment_score'] - prev_report.avg_sentiment_score

        # 키워드 추출
        top_keywords = self._extract_keywords(mentions)

        # AI 요약 생성
        summary = self._generate_summary(teacher_id, stats, mentions)

        # 리포트 저장/업데이트
        existing = self.db.query(DailyReport).filter(
            and_(
                DailyReport.teacher_id == teacher_id,
                DailyReport.report_date == report_date
            )
        ).first()

        if existing:
            report = existing
        else:
            report = DailyReport(
                teacher_id=teacher_id,
                report_date=report_date
            )
            self.db.add(report)

        # 값 설정
        report.mention_count = stats['mention_count']
        report.post_mention_count = stats['post_mention_count']
        report.comment_mention_count = stats['comment_mention_count']
        report.positive_count = stats['positive_count']
        report.negative_count = stats['negative_count']
        report.neutral_count = stats['neutral_count']
        report.avg_sentiment_score = stats['avg_sentiment_score']
        report.difficulty_easy_count = stats['difficulty_easy_count']
        report.difficulty_medium_count = stats['difficulty_medium_count']
        report.difficulty_hard_count = stats['difficulty_hard_count']
        report.recommendation_count = stats['recommendation_count']
        report.mention_change = mention_change
        report.sentiment_change = sentiment_change
        report.summary = summary
        report.top_keywords = top_keywords

        self.db.commit()
        self.db.refresh(report)

        return report

    def generate_academy_stats(
        self,
        academy_id: int,
        report_date: date = None
    ) -> Optional[AcademyDailyStats]:
        """
        학원별 데일리 통계 생성

        Args:
            academy_id: 학원 ID
            report_date: 리포트 날짜 (기본: 오늘)

        Returns:
            생성된 AcademyDailyStats
        """
        if report_date is None:
            report_date = date.today()

        # 해당 학원 강사들의 당일 리포트 조회
        reports = self.db.query(DailyReport).join(Teacher).filter(
            and_(
                Teacher.academy_id == academy_id,
                DailyReport.report_date == report_date
            )
        ).all()

        if not reports:
            return None

        # 통계 계산
        total_mentions = sum(r.mention_count or 0 for r in reports)
        total_teachers = len([r for r in reports if r.mention_count and r.mention_count > 0])

        # 평균 감성 점수
        scores = [r.avg_sentiment_score for r in reports if r.avg_sentiment_score is not None]
        avg_sentiment = sum(scores) / len(scores) if scores else None

        # 최다 언급 강사
        top_teacher_id = None
        if reports:
            top_report = max(reports, key=lambda r: r.mention_count or 0)
            if top_report.mention_count and top_report.mention_count > 0:
                top_teacher_id = top_report.teacher_id

        # 저장/업데이트
        existing = self.db.query(AcademyDailyStats).filter(
            and_(
                AcademyDailyStats.academy_id == academy_id,
                AcademyDailyStats.report_date == report_date
            )
        ).first()

        if existing:
            stats = existing
        else:
            stats = AcademyDailyStats(
                academy_id=academy_id,
                report_date=report_date
            )
            self.db.add(stats)

        stats.total_mentions = total_mentions
        stats.total_teachers_mentioned = total_teachers
        stats.avg_sentiment_score = avg_sentiment
        stats.top_teacher_id = top_teacher_id

        self.db.commit()
        self.db.refresh(stats)

        return stats

    def generate_all_reports(self, report_date: date = None) -> Dict[str, int]:
        """
        모든 강사 및 학원의 데일리 리포트 생성

        Returns:
            생성 통계 (teacher_reports, academy_stats)
        """
        if report_date is None:
            report_date = date.today()

        stats = {
            'teacher_reports': 0,
            'academy_stats': 0
        }

        # 활성 강사 목록
        teachers = self.db.query(Teacher).filter(Teacher.is_active == True).all()

        print(f"\n[*] Generating reports for {report_date}")
        print(f"[-] Processing {len(teachers)} teachers...")

        for teacher in teachers:
            report = self.generate_teacher_report(teacher.id, report_date)
            if report:
                stats['teacher_reports'] += 1
                print(f"    - {teacher.name}: {report.mention_count} mentions")

        # 학원별 통계
        academies = self.db.query(Academy).filter(Academy.is_active == True).all()

        print(f"[-] Processing {len(academies)} academies...")

        for academy in academies:
            academy_stats = self.generate_academy_stats(academy.id, report_date)
            if academy_stats:
                stats['academy_stats'] += 1
                print(f"    - {academy.name}: {academy_stats.total_mentions} total mentions")

        print(f"\n[*] Report generation complete")
        print(f"    Teacher reports: {stats['teacher_reports']}")
        print(f"    Academy stats: {stats['academy_stats']}")

        return stats

    def _calculate_stats(self, mentions: List[TeacherMention]) -> Dict[str, Any]:
        """멘션 통계 계산"""
        stats = {
            'mention_count': len(mentions),
            'post_mention_count': 0,
            'comment_mention_count': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'avg_sentiment_score': None,
            'difficulty_easy_count': 0,
            'difficulty_medium_count': 0,
            'difficulty_hard_count': 0,
            'recommendation_count': 0
        }

        scores = []

        for m in mentions:
            # 멘션 타입별 카운트
            if m.mention_type in ('title', 'content'):
                stats['post_mention_count'] += 1
            elif m.mention_type == 'comment':
                stats['comment_mention_count'] += 1

            # 감성 카운트
            if m.sentiment == 'POSITIVE':
                stats['positive_count'] += 1
            elif m.sentiment == 'NEGATIVE':
                stats['negative_count'] += 1
            else:
                stats['neutral_count'] += 1

            # 감성 점수
            if m.sentiment_score is not None:
                scores.append(m.sentiment_score)

            # 난이도 카운트
            if m.difficulty == 'EASY':
                stats['difficulty_easy_count'] += 1
            elif m.difficulty == 'MEDIUM':
                stats['difficulty_medium_count'] += 1
            elif m.difficulty == 'HARD':
                stats['difficulty_hard_count'] += 1

            # 추천 카운트
            if m.is_recommended:
                stats['recommendation_count'] += 1

        # 평균 감성 점수
        if scores:
            stats['avg_sentiment_score'] = round(sum(scores) / len(scores), 3)

        return stats

    def _get_previous_report(self, teacher_id: int, report_date: date) -> Optional[DailyReport]:
        """전일 리포트 조회"""
        prev_date = report_date - timedelta(days=1)
        return self.db.query(DailyReport).filter(
            and_(
                DailyReport.teacher_id == teacher_id,
                DailyReport.report_date == prev_date
            )
        ).first()

    def _extract_keywords(self, mentions: List[TeacherMention], top_n: int = 5) -> List[str]:
        """자주 등장하는 키워드 추출"""
        # 간단한 키워드 추출 (context에서 명사 추출)
        # 실제 구현에서는 형태소 분석기 사용 권장

        # 주요 키워드 목록 (수동 정의)
        keyword_candidates = [
            '추천', '강추', '비추', '합격', '불합격',
            '기초', '심화', '개념', '문풀', '기출',
            '쉬움', '어려움', '명강의', '꿀강', '노잼',
            '인강', '현강', '독학', '학원', '교재',
            '국어', '영어', '한국사', '행정법', '행정학'
        ]

        word_counts = Counter()

        for m in mentions:
            context = (m.context or '').lower()
            for keyword in keyword_candidates:
                if keyword in context:
                    word_counts[keyword] += 1

        # 상위 N개 반환
        return [word for word, _ in word_counts.most_common(top_n)]

    def _generate_summary(
        self,
        teacher_id: int,
        stats: Dict[str, Any],
        mentions: List[TeacherMention]
    ) -> str:
        """AI 요약 생성 (간단한 템플릿 기반)"""
        teacher = self.db.query(Teacher).filter(Teacher.id == teacher_id).first()
        if not teacher:
            return ""

        # 감성 비율
        total = stats['positive_count'] + stats['negative_count'] + stats['neutral_count']
        if total == 0:
            return f"{teacher.name} 강사 관련 언급이 없습니다."

        positive_ratio = stats['positive_count'] / total * 100
        negative_ratio = stats['negative_count'] / total * 100

        # 요약 생성
        parts = []

        # 언급량
        parts.append(f"총 {stats['mention_count']}회 언급")

        # 감성 분석
        if positive_ratio > 60:
            parts.append(f"긍정적 반응 우세 ({positive_ratio:.0f}%)")
        elif negative_ratio > 40:
            parts.append(f"부정적 반응 다수 ({negative_ratio:.0f}%)")
        else:
            parts.append("중립적 반응 위주")

        # 난이도
        difficulty_total = (stats['difficulty_easy_count'] +
                          stats['difficulty_medium_count'] +
                          stats['difficulty_hard_count'])
        if difficulty_total > 0:
            if stats['difficulty_easy_count'] > stats['difficulty_hard_count']:
                parts.append("강의 난이도: 쉬움")
            elif stats['difficulty_hard_count'] > stats['difficulty_easy_count']:
                parts.append("강의 난이도: 어려움")
            else:
                parts.append("강의 난이도: 보통")

        # 추천
        if stats['recommendation_count'] > 0:
            parts.append(f"추천 언급 {stats['recommendation_count']}회")

        return f"{teacher.name} 강사: " + ", ".join(parts)

    def get_report_summary(self, report_date: date = None) -> Dict[str, Any]:
        """날짜별 전체 리포트 요약"""
        if report_date is None:
            report_date = date.today()

        # 강사별 리포트
        reports = self.db.query(DailyReport).filter(
            DailyReport.report_date == report_date
        ).all()

        # 학원별 통계
        academy_stats = self.db.query(AcademyDailyStats).filter(
            AcademyDailyStats.report_date == report_date
        ).all()

        # 전체 통계
        total_mentions = sum(r.mention_count or 0 for r in reports)
        total_positive = sum(r.positive_count or 0 for r in reports)
        total_negative = sum(r.negative_count or 0 for r in reports)
        total_recommendations = sum(r.recommendation_count or 0 for r in reports)

        # 상위 언급 강사
        top_teachers = sorted(
            [r for r in reports if r.mention_count],
            key=lambda r: r.mention_count,
            reverse=True
        )[:10]

        # 감성 변화가 큰 강사
        sentiment_changes = sorted(
            [r for r in reports if r.sentiment_change is not None],
            key=lambda r: abs(r.sentiment_change),
            reverse=True
        )[:5]

        return {
            'report_date': report_date,
            'total_teachers_reported': len(reports),
            'total_academies_reported': len(academy_stats),
            'total_mentions': total_mentions,
            'total_positive': total_positive,
            'total_negative': total_negative,
            'total_recommendations': total_recommendations,
            'positive_ratio': total_positive / total_mentions * 100 if total_mentions > 0 else 0,
            'top_mentioned_teachers': [
                {
                    'teacher_id': r.teacher_id,
                    'mention_count': r.mention_count,
                    'sentiment_score': r.avg_sentiment_score
                }
                for r in top_teachers
            ],
            'biggest_sentiment_changes': [
                {
                    'teacher_id': r.teacher_id,
                    'sentiment_change': r.sentiment_change,
                    'current_score': r.avg_sentiment_score
                }
                for r in sentiment_changes
            ]
        }
