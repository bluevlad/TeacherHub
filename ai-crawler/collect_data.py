# -*- coding: utf-8 -*-
"""
TeacherHub 실제 데이터 수집 스크립트
등록된 강사들의 게시글을 수집하고 DB에 저장
"""
import asyncio
import sys
import os
from datetime import datetime
from urllib.parse import quote

# 프로젝트 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import execute_values


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


def get_teachers(conn):
    """활성화된 강사 목록 조회 (국어/영어/한국사만)"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT t.id, t.name, t.aliases, a.name as academy, s.name as subject
            FROM teachers t
            JOIN academies a ON t.academy_id = a.id
            JOIN subjects s ON t.subject_id = s.id
            WHERE t.is_active = TRUE
              AND a.is_active = TRUE
              AND s.name IN ('국어', '영어', '한국사')
            ORDER BY a.name, s.name, t.name
        """)
        return cur.fetchall()


def get_sources(conn):
    """활성화된 수집 소스 조회"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, name, code, base_url, source_type, config
            FROM collection_sources
            WHERE is_active = TRUE AND source_type = 'gallery'
        """)
        return cur.fetchall()


def save_post(conn, source_id, post_data):
    """게시글 저장 (중복 시 업데이트)"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO posts (source_id, external_id, title, content, url, author, post_date,
                             view_count, like_count, comment_count, collected_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (source_id, external_id)
            DO UPDATE SET
                view_count = EXCLUDED.view_count,
                like_count = EXCLUDED.like_count,
                comment_count = EXCLUDED.comment_count,
                collected_at = NOW()
            RETURNING id
        """, (
            source_id,
            post_data['external_id'],
            post_data['title'],
            post_data.get('content', ''),
            post_data['url'],
            post_data.get('author', ''),
            post_data.get('post_date'),
            post_data.get('view_count', 0),
            post_data.get('like_count', 0),
            post_data.get('comment_count', 0)
        ))
        result = cur.fetchone()
        conn.commit()
        return result[0] if result else None


def save_comments(conn, post_id, comments):
    """댓글 저장"""
    if not comments:
        return

    with conn.cursor() as cur:
        for cmt in comments:
            cur.execute("""
                INSERT INTO comments (post_id, external_id, content, author, comment_date, collected_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT DO NOTHING
            """, (
                post_id,
                cmt.get('external_id', ''),
                cmt.get('content', ''),
                cmt.get('author', ''),
                cmt.get('comment_date')
            ))
        conn.commit()


def save_mention(conn, teacher_id, post_id, comment_id, mention_type, matched_text, context):
    """강사 멘션 저장"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO teacher_mentions
                (teacher_id, post_id, comment_id, mention_type, matched_text, context, analyzed_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
        """, (teacher_id, post_id, comment_id, mention_type, matched_text, context))
        conn.commit()


def find_teacher_mentions(text, teachers):
    """텍스트에서 강사 멘션 찾기"""
    mentions = []
    if not text:
        return mentions

    for teacher in teachers:
        teacher_id, name, aliases, academy, subject = teacher

        # 이름 검색
        search_terms = [name]
        if aliases:
            search_terms.extend(aliases)

        for term in search_terms:
            if term and term in text:
                # 주변 문맥 추출 (앞뒤 50자)
                idx = text.find(term)
                start = max(0, idx - 50)
                end = min(len(text), idx + len(term) + 50)
                context = text[start:end]

                mentions.append({
                    'teacher_id': teacher_id,
                    'matched_text': term,
                    'context': context
                })
                break  # 한 강사당 하나의 멘션만

    return mentions


async def crawl_gallery(gallery_type, gallery_id, keyword, limit=20):
    """DC Inside 갤러리 크롤링"""

    if gallery_type == 'mgallery':
        base_url = f"https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}"
    else:
        base_url = f"https://gall.dcinside.com/board/lists/?id={gallery_id}"

    search_url = f"{base_url}&s_type=search_subject_memo&s_keyword={quote(keyword)}"

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="ko-KR"
    )
    page = await context.new_page()

    results = []

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')

        rows = soup.select("tr.ub-content")

        for row in rows:
            try:
                num_elem = row.select_one("td.gall_num")
                if not num_elem:
                    continue
                external_id = num_elem.get_text(strip=True)
                if not external_id.isdigit():
                    continue

                title_elem = row.select_one("td.gall_tit a")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')

                if href.startswith('javascript'):
                    continue

                url = f"https://gall.dcinside.com{href}" if href.startswith('/') else href

                writer_elem = row.select_one("td.gall_writer .nickname")
                author = ''
                if writer_elem:
                    author = writer_elem.get('title', '') or writer_elem.get_text(strip=True)

                date_elem = row.select_one("td.gall_date")
                date_str = date_elem.get('title', '') if date_elem else ''
                post_date = None
                if date_str and len(date_str) >= 10:
                    try:
                        post_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                    except:
                        pass

                view_elem = row.select_one("td.gall_count")
                view_count = 0
                if view_elem:
                    try:
                        view_count = int(view_elem.get_text(strip=True).replace('-', '0'))
                    except:
                        pass

                rec_elem = row.select_one("td.gall_recommend")
                like_count = 0
                if rec_elem:
                    try:
                        like_count = int(rec_elem.get_text(strip=True).replace('-', '0'))
                    except:
                        pass

                results.append({
                    'external_id': external_id,
                    'title': title,
                    'url': url,
                    'author': author,
                    'post_date': post_date,
                    'view_count': view_count,
                    'like_count': like_count,
                    'comment_count': 0,
                    'content': '',
                    'comments': []
                })

                if len(results) >= limit:
                    break

            except Exception as e:
                continue

        # 상세 페이지 크롤링
        for post in results[:10]:  # 상위 10개만 상세 수집
            try:
                await page.goto(post['url'], wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(1500)

                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')

                content_elem = soup.select_one(".write_div")
                if content_elem:
                    for tag in content_elem.select('img, video, iframe, script, style'):
                        tag.decompose()
                    post['content'] = content_elem.get_text(strip=True)

                comments = []
                for idx, cmt in enumerate(soup.select(".cmt_info")):
                    content_elem = cmt.select_one(".usertxt")
                    author_elem = cmt.select_one(".gall_writer .nickname")

                    if content_elem:
                        comments.append({
                            'external_id': str(idx),
                            'content': content_elem.get_text(strip=True),
                            'author': author_elem.get('title', '') if author_elem else '',
                            'comment_date': None
                        })

                post['comments'] = comments
                post['comment_count'] = len(comments)

            except Exception as e:
                continue

    finally:
        await browser.close()
        await playwright.stop()

    return results


async def collect_teacher_data(conn, teacher, sources):
    """특정 강사의 데이터 수집"""
    teacher_id, name, aliases, academy, subject = teacher

    print(f"\n  [{academy}] {name} ({subject})")

    total_posts = 0
    total_mentions = 0

    for source in sources:
        source_id, source_name, source_code, base_url, source_type, config = source

        # 갤러리 정보 파싱 (psycopg2는 JSONB를 자동으로 dict로 변환)
        cfg = config if isinstance(config, dict) else {}
        gallery_id = cfg.get('gallery_id', 'gosi')
        gallery_type = cfg.get('gallery_type', 'mgallery')

        print(f"    - {source_name}: ", end="", flush=True)

        try:
            posts = await crawl_gallery(gallery_type, gallery_id, name, limit=15)

            for post in posts:
                # 게시글 저장
                post_id = save_post(conn, source_id, post)

                if post_id:
                    total_posts += 1

                    # 댓글 저장
                    save_comments(conn, post_id, post.get('comments', []))

                    # 제목에서 멘션 찾기
                    mentions = find_teacher_mentions(post['title'], [teacher])
                    for m in mentions:
                        save_mention(conn, m['teacher_id'], post_id, None, 'title', m['matched_text'], m['context'])
                        total_mentions += 1

                    # 본문에서 멘션 찾기
                    if post.get('content'):
                        mentions = find_teacher_mentions(post['content'], [teacher])
                        for m in mentions:
                            save_mention(conn, m['teacher_id'], post_id, None, 'content', m['matched_text'], m['context'])
                            total_mentions += 1

            print(f"{len(posts)}건 수집")

        except Exception as e:
            print(f"오류 - {e}")

    return total_posts, total_mentions


async def main():
    """메인 수집 함수"""
    print("=" * 60)
    print("TeacherHub 데이터 수집 시작")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = get_db_connection()

    try:
        # 강사 목록 조회
        teachers = get_teachers(conn)
        print(f"\n[1] 등록된 강사: {len(teachers)}명")

        # 수집 소스 조회
        sources = get_sources(conn)
        print(f"[2] 수집 소스: {len(sources)}개")

        for src in sources:
            print(f"    - {src[1]} ({src[2]})")

        # 크롤링 로그 시작
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO crawl_logs (source_id, started_at, status)
                VALUES (%s, NOW(), 'running')
                RETURNING id
            """, (sources[0][0],))
            crawl_log_id = cur.fetchone()[0]
            conn.commit()

        # 강사별 데이터 수집
        print(f"\n[3] 강사별 데이터 수집 시작")
        print("-" * 60)

        total_posts = 0
        total_mentions = 0

        for teacher in teachers:
            posts, mentions = await collect_teacher_data(conn, teacher, sources)
            total_posts += posts
            total_mentions += mentions

            # 과부하 방지
            await asyncio.sleep(2)

        # 크롤링 로그 업데이트
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE crawl_logs
                SET finished_at = NOW(),
                    status = 'completed',
                    posts_collected = %s,
                    mentions_found = %s
                WHERE id = %s
            """, (total_posts, total_mentions, crawl_log_id))
            conn.commit()

        # 결과 요약
        print("\n" + "=" * 60)
        print("수집 완료")
        print("=" * 60)
        print(f"  총 게시글: {total_posts}건")
        print(f"  총 멘션: {total_mentions}건")

        # DB 통계
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM posts")
            db_posts = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM comments")
            db_comments = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM teacher_mentions")
            db_mentions = cur.fetchone()[0]

        print(f"\n[DB 현황]")
        print(f"  게시글: {db_posts}건")
        print(f"  댓글: {db_comments}건")
        print(f"  멘션: {db_mentions}건")

        print(f"\n완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())
