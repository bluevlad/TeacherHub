# -*- coding: utf-8 -*-
"""
TeacherHub 감성 분석 스크립트
수집된 멘션에 대한 긍정/부정 분석
"""
import os
import sys
from datetime import datetime, date
import psycopg2


# DB 연결 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'teacherhub'),
    'user': os.getenv('DB_USER', 'teacherhub'),
    'password': os.environ['DB_PASSWORD']
}


def get_db_connection():
    """DB 연결"""
    return psycopg2.connect(**DB_CONFIG)


def get_keywords(conn):
    """분석 키워드 조회"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT category, keyword, weight
            FROM analysis_keywords
            WHERE is_active = TRUE
        """)
        rows = cur.fetchall()

    keywords = {'positive': [], 'negative': []}
    for category, keyword, weight in rows:
        if 'positive' in category:
            keywords['positive'].append((keyword, weight))
        elif 'negative' in category:
            keywords['negative'].append((keyword, weight))

    return keywords


def analyze_text(text, keywords):
    """텍스트 감성 분석"""
    if not text:
        return 'NEUTRAL', 0.0, [], []

    text_lower = text.lower()

    positive_matches = []
    negative_matches = []
    positive_score = 0.0
    negative_score = 0.0

    # 긍정 키워드 검색
    for keyword, weight in keywords['positive']:
        if keyword in text:
            positive_matches.append(keyword)
            positive_score += weight

    # 부정 키워드 검색
    for keyword, weight in keywords['negative']:
        if keyword in text:
            negative_matches.append(keyword)
            negative_score += weight

    # 감성 판정
    if positive_score == 0 and negative_score == 0:
        sentiment = 'NEUTRAL'
        score = 0.0
    elif positive_score > negative_score:
        sentiment = 'POSITIVE'
        score = min(1.0, (positive_score - negative_score) / max(positive_score, 1))
    elif negative_score > positive_score:
        sentiment = 'NEGATIVE'
        score = max(-1.0, (positive_score - negative_score) / max(negative_score, 1))
    else:
        sentiment = 'NEUTRAL'
        score = 0.0

    return sentiment, score, positive_matches, negative_matches


def get_mentions_with_context(conn):
    """분석할 멘션 조회 (본문 포함)"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                tm.id,
                tm.teacher_id,
                tm.context,
                p.title,
                p.content,
                t.name as teacher_name
            FROM teacher_mentions tm
            JOIN posts p ON tm.post_id = p.id
            JOIN teachers t ON tm.teacher_id = t.id
            WHERE tm.sentiment IS NULL OR tm.sentiment = ''
        """)
        return cur.fetchall()


def update_mention_sentiment(conn, mention_id, sentiment, score, is_recommended):
    """멘션 감성 분석 결과 업데이트"""
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE teacher_mentions
            SET sentiment = %s,
                sentiment_score = %s,
                is_recommended = %s,
                analyzed_at = NOW()
            WHERE id = %s
        """, (sentiment, score, is_recommended, mention_id))
    conn.commit()


def generate_daily_report(conn, teacher_id, report_date):
    """강사별 일간 리포트 생성"""
    with conn.cursor() as cur:
        # 멘션 통계 조회
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE sentiment = 'POSITIVE') as positive,
                COUNT(*) FILTER (WHERE sentiment = 'NEGATIVE') as negative,
                COUNT(*) FILTER (WHERE sentiment = 'NEUTRAL') as neutral,
                AVG(sentiment_score) as avg_score,
                COUNT(*) FILTER (WHERE is_recommended = TRUE) as recommendations,
                COUNT(*) FILTER (WHERE mention_type = 'title') as title_mentions,
                COUNT(*) FILTER (WHERE mention_type = 'content') as content_mentions,
                COUNT(*) FILTER (WHERE mention_type = 'comment') as comment_mentions
            FROM teacher_mentions tm
            JOIN posts p ON tm.post_id = p.id
            WHERE tm.teacher_id = %s
              AND DATE(p.collected_at) = %s
        """, (teacher_id, report_date))

        stats = cur.fetchone()
        if not stats or stats[0] == 0:
            return None

        total, positive, negative, neutral, avg_score, recommendations, \
            title_mentions, content_mentions, comment_mentions = stats

        # 요약 생성
        if positive > negative:
            summary = f"긍정적 평가가 우세합니다. (긍정 {positive}건, 부정 {negative}건)"
        elif negative > positive:
            summary = f"부정적 평가가 있습니다. (긍정 {positive}건, 부정 {negative}건)"
        else:
            summary = f"중립적 평가입니다. (긍정 {positive}건, 부정 {negative}건)"

        # 리포트 저장
        cur.execute("""
            INSERT INTO daily_reports (
                report_date, teacher_id, mention_count,
                post_mention_count, comment_mention_count,
                positive_count, negative_count, neutral_count,
                avg_sentiment_score, recommendation_count, summary
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (report_date, teacher_id)
            DO UPDATE SET
                mention_count = EXCLUDED.mention_count,
                positive_count = EXCLUDED.positive_count,
                negative_count = EXCLUDED.negative_count,
                neutral_count = EXCLUDED.neutral_count,
                avg_sentiment_score = EXCLUDED.avg_sentiment_score,
                recommendation_count = EXCLUDED.recommendation_count,
                summary = EXCLUDED.summary
            RETURNING id
        """, (
            report_date, teacher_id, total,
            title_mentions + content_mentions, comment_mentions,
            positive, negative, neutral,
            avg_score or 0, recommendations, summary
        ))

        conn.commit()
        return cur.fetchone()[0]


def main():
    """메인 감성 분석 함수"""
    print("=" * 60)
    print("TeacherHub 감성 분석 시작")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = get_db_connection()

    try:
        # 1. 키워드 로드
        keywords = get_keywords(conn)
        print(f"\n[1] 분석 키워드 로드")
        print(f"    긍정 키워드: {len(keywords['positive'])}개")
        print(f"    부정 키워드: {len(keywords['negative'])}개")

        # 2. 멘션 조회
        mentions = get_mentions_with_context(conn)
        print(f"\n[2] 분석 대상 멘션: {len(mentions)}건")

        # 3. 감성 분석 실행
        print(f"\n[3] 감성 분석 실행")
        print("-" * 60)

        results = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
        sample_results = []

        for mention_id, teacher_id, context, title, content, teacher_name in mentions:
            # 분석할 텍스트 준비 (컨텍스트 + 제목 + 본문)
            analysis_text = f"{context or ''} {title or ''} {content or ''}"

            # 감성 분석
            sentiment, score, pos_matches, neg_matches = analyze_text(analysis_text, keywords)

            # 추천 여부 판단
            is_recommended = any(kw in analysis_text for kw in ['추천', '강추', '들어라', '필수'])

            # DB 업데이트
            update_mention_sentiment(conn, mention_id, sentiment, score, is_recommended)

            results[sentiment] += 1

            # 샘플 저장 (처음 몇 개)
            if len(sample_results) < 10 and (pos_matches or neg_matches):
                sample_results.append({
                    'teacher': teacher_name,
                    'sentiment': sentiment,
                    'score': score,
                    'positive': pos_matches,
                    'negative': neg_matches,
                    'context': (context or '')[:50]
                })

        print(f"    긍정: {results['POSITIVE']}건")
        print(f"    부정: {results['NEGATIVE']}건")
        print(f"    중립: {results['NEUTRAL']}건")

        # 4. 샘플 결과 출력
        if sample_results:
            print(f"\n[4] 분석 샘플 (키워드 매칭된 건)")
            print("-" * 60)
            for i, r in enumerate(sample_results, 1):
                print(f"\n  [{i}] {r['teacher']} - {r['sentiment']} (점수: {r['score']:.2f})")
                if r['positive']:
                    print(f"      긍정 키워드: {', '.join(r['positive'])}")
                if r['negative']:
                    print(f"      부정 키워드: {', '.join(r['negative'])}")
                print(f"      문맥: {r['context']}...")

        # 5. 일간 리포트 생성
        print(f"\n[5] 일간 리포트 생성")
        print("-" * 60)

        today = date.today()

        # 분석된 강사 목록 조회
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT t.id, t.name, a.name as academy
                FROM teacher_mentions tm
                JOIN teachers t ON tm.teacher_id = t.id
                JOIN academies a ON t.academy_id = a.id
            """)
            teachers = cur.fetchall()

        report_count = 0
        for teacher_id, teacher_name, academy in teachers:
            report_id = generate_daily_report(conn, teacher_id, today)
            if report_id:
                report_count += 1

        print(f"    생성된 리포트: {report_count}건")

        # 6. 최종 결과 요약
        print(f"\n" + "=" * 60)
        print("감성 분석 완료")
        print("=" * 60)

        # 강사별 감성 점수 조회
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    t.name as "강사",
                    a.name as "학원",
                    COUNT(tm.id) as "멘션수",
                    COUNT(*) FILTER (WHERE tm.sentiment = 'POSITIVE') as "긍정",
                    COUNT(*) FILTER (WHERE tm.sentiment = 'NEGATIVE') as "부정",
                    ROUND(AVG(tm.sentiment_score)::numeric, 2) as "평균점수"
                FROM teachers t
                JOIN academies a ON t.academy_id = a.id
                LEFT JOIN teacher_mentions tm ON t.id = tm.teacher_id
                WHERE tm.id IS NOT NULL
                GROUP BY t.name, a.name
                ORDER BY COUNT(tm.id) DESC
            """)
            teacher_stats = cur.fetchall()

        print(f"\n[강사별 감성 분석 결과]")
        print("-" * 60)
        print(f"{'강사':<10} {'학원':<12} {'멘션':<6} {'긍정':<6} {'부정':<6} {'점수':<8}")
        print("-" * 60)

        for name, academy, mentions, positive, negative, avg_score in teacher_stats:
            academy_short = academy[:10] if len(academy) > 10 else academy
            print(f"{name:<10} {academy_short:<12} {mentions:<6} {positive:<6} {negative:<6} {avg_score or 0:<8}")

        print(f"\n완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
