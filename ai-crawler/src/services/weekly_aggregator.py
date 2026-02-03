"""
Weekly Aggregator Service
주간 데이터 집계 서비스

- 일별 리포트를 주간 리포트로 집계
- 전주 대비 변화율 계산
- 순위 산정
- 하이브리드 조회 (완료된 주 + 현재 주 실시간)
"""
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from ..models import (
    Teacher, Academy, DailyReport, WeeklyReport,
    AcademyWeeklyStats, AggregationLog
)
from ..database import get_session

logger = logging.getLogger(__name__)


class WeeklyAggregator:
    """주간 데이터 집계 서비스"""

    def __init__(self, session: Session = None):
        self._session = session
        self._own_session = session is None

    def __enter__(self):
        if self._own_session:
            self._session = get_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_session and self._session:
            self._session.close()

    @property
    def session(self) -> Session:
        return self._session

    @staticmethod
    def get_week_range(target_date: date = None) -> Tuple[date, date, int, int]:
        """
        주어진 날짜의 주간 범위 계산 (ISO week 기준)

        Returns:
            (week_start, week_end, year, week_number)
        """
        if target_date is None:
            target_date = date.today()

        # ISO week: 월요일 시작
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)

        iso_calendar = target_date.isocalendar()
        year = iso_calendar[0]
        week_number = iso_calendar[1]

        return week_start, week_end, year, week_number

    @staticmethod
    def get_previous_week_range(target_date: date = None) -> Tuple[date, date, int, int]:
        """전주 범위 계산"""
        if target_date is None:
            target_date = date.today()

        previous_week_date = target_date - timedelta(days=7)
        return WeeklyAggregator.get_week_range(previous_week_date)

    def aggregate_weekly_reports(self, target_date: date = None) -> int:
        """
        주간 리포트 집계 실행

        Args:
            target_date: 집계 대상 날짜 (None이면 전주)

        Returns:
            집계된 리포트 수
        """
        if target_date is None:
            # 기본: 전주 집계
            target_date = date.today() - timedelta(days=7)

        week_start, week_end, year, week_number = self.get_week_range(target_date)

        logger.info(f"Starting weekly aggregation: {year} W{week_number} ({week_start} ~ {week_end})")

        # 집계 로그 생성
        agg_log = AggregationLog(
            aggregation_type='weekly',
            target_date=target_date,
            year=year,
            week_number=week_number,
            status='running',
            started_at=datetime.now()
        )
        self.session.add(agg_log)
        self.session.flush()

        try:
            # 1. 활성 강사 목록 조회
            teachers = self.session.query(Teacher).filter(
                Teacher.is_active == True
            ).all()

            processed_count = 0

            for teacher in teachers:
                report = self._aggregate_teacher_weekly(
                    teacher, week_start, week_end, year, week_number
                )
                if report:
                    processed_count += 1

            # 2. 순위 계산
            self._calculate_weekly_ranks(year, week_number)

            # 3. 학원별 통계 집계
            self._aggregate_academy_stats(week_start, week_end, year, week_number)

            # 4. 집계 완료 표시
            self.session.query(WeeklyReport).filter(
                WeeklyReport.year == year,
                WeeklyReport.week_number == week_number
            ).update({'is_complete': True})

            self.session.commit()

            # 로그 업데이트
            agg_log.status = 'completed'
            agg_log.completed_at = datetime.now()
            agg_log.records_processed = processed_count
            self.session.commit()

            logger.info(f"Weekly aggregation completed: {processed_count} reports")
            return processed_count

        except Exception as e:
            logger.error(f"Weekly aggregation failed: {e}")
            self.session.rollback()

            agg_log.status = 'failed'
            agg_log.completed_at = datetime.now()
            agg_log.error_message = str(e)
            self.session.commit()

            raise

    def _aggregate_teacher_weekly(
        self,
        teacher: Teacher,
        week_start: date,
        week_end: date,
        year: int,
        week_number: int
    ) -> Optional[WeeklyReport]:
        """개별 강사 주간 집계"""

        # 해당 주 일별 리포트 조회
        daily_reports = self.session.query(DailyReport).filter(
            DailyReport.teacher_id == teacher.id,
            DailyReport.report_date >= week_start,
            DailyReport.report_date <= week_end
        ).all()

        if not daily_reports:
            return None

        # 기존 주간 리포트 확인
        existing = self.session.query(WeeklyReport).filter(
            WeeklyReport.teacher_id == teacher.id,
            WeeklyReport.year == year,
            WeeklyReport.week_number == week_number
        ).first()

        if existing:
            report = existing
        else:
            report = WeeklyReport(
                teacher_id=teacher.id,
                academy_id=teacher.academy_id,
                year=year,
                week_number=week_number,
                week_start_date=week_start,
                week_end_date=week_end
            )
            self.session.add(report)

        # 통계 집계
        report.mention_count = sum(r.mention_count or 0 for r in daily_reports)
        report.positive_count = sum(r.positive_count or 0 for r in daily_reports)
        report.negative_count = sum(r.negative_count or 0 for r in daily_reports)
        report.neutral_count = sum(r.neutral_count or 0 for r in daily_reports)
        report.recommendation_count = sum(r.recommendation_count or 0 for r in daily_reports)

        report.difficulty_easy_count = sum(r.difficulty_easy_count or 0 for r in daily_reports)
        report.difficulty_medium_count = sum(r.difficulty_medium_count or 0 for r in daily_reports)
        report.difficulty_hard_count = sum(r.difficulty_hard_count or 0 for r in daily_reports)

        # 평균 감성 점수 계산
        sentiment_scores = [r.avg_sentiment_score for r in daily_reports if r.avg_sentiment_score]
        if sentiment_scores:
            report.avg_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)

        # 전주 대비 변화율 계산
        prev_week_start, prev_week_end, prev_year, prev_week_num = self.get_previous_week_range(week_start)
        prev_report = self.session.query(WeeklyReport).filter(
            WeeklyReport.teacher_id == teacher.id,
            WeeklyReport.year == prev_year,
            WeeklyReport.week_number == prev_week_num
        ).first()

        if prev_report and prev_report.mention_count > 0:
            change = ((report.mention_count - prev_report.mention_count) / prev_report.mention_count) * 100
            report.mention_change_rate = round(change, 2)

            if prev_report.avg_sentiment_score:
                report.sentiment_trend = report.avg_sentiment_score - prev_report.avg_sentiment_score

        # 키워드 집계
        all_keywords = {}
        for dr in daily_reports:
            if dr.top_keywords:
                for kw in dr.top_keywords:
                    all_keywords[kw] = all_keywords.get(kw, 0) + 1

        report.top_keywords = sorted(all_keywords.keys(), key=lambda k: all_keywords[k], reverse=True)[:10]

        # 요일별 분포
        daily_dist = {}
        for dr in daily_reports:
            day_name = dr.report_date.strftime('%A')
            daily_dist[day_name] = dr.mention_count or 0
        report.daily_distribution = daily_dist

        report.aggregated_at = datetime.now()

        return report

    def _calculate_weekly_ranks(self, year: int, week_number: int):
        """주간 순위 계산"""

        # 전체 순위 (언급수 기준)
        reports = self.session.query(WeeklyReport).filter(
            WeeklyReport.year == year,
            WeeklyReport.week_number == week_number
        ).order_by(WeeklyReport.mention_count.desc()).all()

        for rank, report in enumerate(reports, 1):
            report.weekly_rank = rank

        # 학원별 순위
        academy_ids = set(r.academy_id for r in reports)
        for academy_id in academy_ids:
            academy_reports = [r for r in reports if r.academy_id == academy_id]
            academy_reports.sort(key=lambda r: r.mention_count or 0, reverse=True)

            for rank, report in enumerate(academy_reports, 1):
                report.academy_rank = rank

    def _aggregate_academy_stats(
        self,
        week_start: date,
        week_end: date,
        year: int,
        week_number: int
    ):
        """학원별 주간 통계 집계"""

        academies = self.session.query(Academy).filter(Academy.is_active == True).all()

        for academy in academies:
            # 해당 학원의 주간 리포트 조회
            reports = self.session.query(WeeklyReport).filter(
                WeeklyReport.academy_id == academy.id,
                WeeklyReport.year == year,
                WeeklyReport.week_number == week_number
            ).all()

            if not reports:
                continue

            # 기존 통계 확인
            existing = self.session.query(AcademyWeeklyStats).filter(
                AcademyWeeklyStats.academy_id == academy.id,
                AcademyWeeklyStats.year == year,
                AcademyWeeklyStats.week_number == week_number
            ).first()

            if existing:
                stats = existing
            else:
                stats = AcademyWeeklyStats(
                    academy_id=academy.id,
                    year=year,
                    week_number=week_number,
                    week_start_date=week_start,
                    week_end_date=week_end
                )
                self.session.add(stats)

            stats.total_mentions = sum(r.mention_count or 0 for r in reports)
            stats.total_teachers_mentioned = len([r for r in reports if r.mention_count > 0])
            stats.total_positive = sum(r.positive_count or 0 for r in reports)
            stats.total_negative = sum(r.negative_count or 0 for r in reports)
            stats.total_recommendations = sum(r.recommendation_count or 0 for r in reports)

            # 평균 감성 점수
            sentiment_scores = [r.avg_sentiment_score for r in reports if r.avg_sentiment_score]
            if sentiment_scores:
                stats.avg_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)

            # TOP 강사
            top_report = max(reports, key=lambda r: r.mention_count or 0)
            if top_report.mention_count > 0:
                stats.top_teacher_id = top_report.teacher_id
                stats.top_teacher_mentions = top_report.mention_count

            # 키워드 집계
            all_keywords = {}
            for r in reports:
                if r.top_keywords:
                    for kw in r.top_keywords:
                        all_keywords[kw] = all_keywords.get(kw, 0) + 1

            stats.top_keywords = sorted(all_keywords.keys(), key=lambda k: all_keywords[k], reverse=True)[:10]
            stats.aggregated_at = datetime.now()

    def get_weekly_report(
        self,
        teacher_id: int,
        year: int = None,
        week_number: int = None,
        include_current_week: bool = True
    ) -> Optional[Dict]:
        """
        주간 리포트 조회 (하이브리드 방식)

        Args:
            teacher_id: 강사 ID
            year: 연도 (None이면 현재)
            week_number: 주차 (None이면 현재)
            include_current_week: 현재 주 실시간 집계 포함 여부
        """
        if year is None or week_number is None:
            _, _, year, week_number = self.get_week_range()

        # 완료된 주간 리포트 조회
        report = self.session.query(WeeklyReport).filter(
            WeeklyReport.teacher_id == teacher_id,
            WeeklyReport.year == year,
            WeeklyReport.week_number == week_number
        ).first()

        if report and report.is_complete:
            return self._report_to_dict(report)

        # 현재 주이고 include_current_week가 True면 실시간 집계
        current_week_start, current_week_end, current_year, current_week = self.get_week_range()

        if include_current_week and year == current_year and week_number == current_week:
            return self._get_realtime_weekly_stats(teacher_id, current_week_start)

        return self._report_to_dict(report) if report else None

    def _get_realtime_weekly_stats(self, teacher_id: int, week_start: date) -> Dict:
        """현재 주 실시간 통계 집계"""

        teacher = self.session.query(Teacher).get(teacher_id)
        if not teacher:
            return None

        daily_reports = self.session.query(DailyReport).filter(
            DailyReport.teacher_id == teacher_id,
            DailyReport.report_date >= week_start,
            DailyReport.report_date <= date.today()
        ).all()

        if not daily_reports:
            return {
                'teacher_id': teacher_id,
                'teacher_name': teacher.name,
                'is_realtime': True,
                'mention_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'recommendation_count': 0
            }

        mention_count = sum(r.mention_count or 0 for r in daily_reports)
        positive_count = sum(r.positive_count or 0 for r in daily_reports)
        negative_count = sum(r.negative_count or 0 for r in daily_reports)
        neutral_count = sum(r.neutral_count or 0 for r in daily_reports)
        recommendation_count = sum(r.recommendation_count or 0 for r in daily_reports)

        sentiment_scores = [r.avg_sentiment_score for r in daily_reports if r.avg_sentiment_score]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        return {
            'teacher_id': teacher_id,
            'teacher_name': teacher.name,
            'academy_name': teacher.academy.name if teacher.academy else None,
            'is_realtime': True,
            'week_start_date': week_start.isoformat(),
            'mention_count': mention_count,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'recommendation_count': recommendation_count,
            'avg_sentiment_score': float(avg_sentiment) if avg_sentiment else None
        }

    def _report_to_dict(self, report: WeeklyReport) -> Dict:
        """WeeklyReport를 딕셔너리로 변환"""
        if not report:
            return None

        return {
            'id': report.id,
            'teacher_id': report.teacher_id,
            'teacher_name': report.teacher.name if report.teacher else None,
            'academy_id': report.academy_id,
            'academy_name': report.academy.name if report.academy else None,
            'year': report.year,
            'week_number': report.week_number,
            'week_start_date': report.week_start_date.isoformat() if report.week_start_date else None,
            'week_end_date': report.week_end_date.isoformat() if report.week_end_date else None,
            'mention_count': report.mention_count,
            'positive_count': report.positive_count,
            'negative_count': report.negative_count,
            'neutral_count': report.neutral_count,
            'recommendation_count': report.recommendation_count,
            'difficulty_easy_count': report.difficulty_easy_count,
            'difficulty_medium_count': report.difficulty_medium_count,
            'difficulty_hard_count': report.difficulty_hard_count,
            'avg_sentiment_score': float(report.avg_sentiment_score) if report.avg_sentiment_score else None,
            'mention_change_rate': float(report.mention_change_rate) if report.mention_change_rate else None,
            'weekly_rank': report.weekly_rank,
            'academy_rank': report.academy_rank,
            'top_keywords': report.top_keywords or [],
            'ai_summary': report.ai_summary,
            'is_complete': report.is_complete,
            'is_realtime': False
        }

    def get_weekly_ranking(
        self,
        year: int = None,
        week_number: int = None,
        academy_id: int = None,
        limit: int = 20
    ) -> List[Dict]:
        """주간 강사 랭킹 조회"""

        if year is None or week_number is None:
            _, _, year, week_number = self.get_week_range()

        query = self.session.query(WeeklyReport).filter(
            WeeklyReport.year == year,
            WeeklyReport.week_number == week_number
        )

        if academy_id:
            query = query.filter(WeeklyReport.academy_id == academy_id)

        reports = query.order_by(WeeklyReport.mention_count.desc()).limit(limit).all()

        return [self._report_to_dict(r) for r in reports]

    def get_trend_data(
        self,
        teacher_id: int,
        weeks: int = 8
    ) -> List[Dict]:
        """강사 주간 트렌드 데이터 조회"""

        reports = self.session.query(WeeklyReport).filter(
            WeeklyReport.teacher_id == teacher_id
        ).order_by(
            WeeklyReport.year.desc(),
            WeeklyReport.week_number.desc()
        ).limit(weeks).all()

        # 오래된 순으로 정렬
        reports.reverse()

        return [{
            'year': r.year,
            'week_number': r.week_number,
            'week_label': f"W{r.week_number}",
            'mention_count': r.mention_count,
            'positive_count': r.positive_count,
            'negative_count': r.negative_count,
            'recommendation_count': r.recommendation_count,
            'avg_sentiment_score': float(r.avg_sentiment_score) if r.avg_sentiment_score else None,
            'weekly_rank': r.weekly_rank
        } for r in reports]


# 편의 함수
def aggregate_last_week():
    """전주 데이터 집계 (스케줄러용)"""
    with WeeklyAggregator() as aggregator:
        return aggregator.aggregate_weekly_reports()


def get_teacher_weekly_summary(teacher_id: int) -> Dict:
    """강사 주간 요약 조회"""
    with WeeklyAggregator() as aggregator:
        return aggregator.get_weekly_report(teacher_id)
