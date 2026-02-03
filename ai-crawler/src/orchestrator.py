"""
Crawler Orchestrator
크롤링 작업 통합 관리
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import CollectionSource, CrawlLog
from .crawlers import NaverCafeCrawler, DCInsideCrawler
from .services import MentionExtractor


class CrawlerOrchestrator:
    """크롤링 작업 오케스트레이터"""

    # 소스 코드별 크롤러 매핑
    CRAWLER_MAP = {
        # 네이버 카페
        'naver_gongstar': ('naver_cafe', 'gongstar'),
        'naver_gongdream': ('naver_cafe', 'm2school'),
        # DC인사이드
        'dcinside_gongmuwon': ('dcinside', 'gongmuwon'),
        'dcinside_gongsilife': ('dcinside', 'gongsilife'),
        'dcinside_government': ('dcinside', 'government'),
    }

    def __init__(self, db: Session = None, naver_id: str = None, naver_pw: str = None):
        self.db = db or SessionLocal()
        self.naver_id = naver_id
        self.naver_pw = naver_pw
        self.extractor = MentionExtractor(self.db)

    def get_active_sources(self) -> List[CollectionSource]:
        """활성화된 수집 소스 목록"""
        return self.db.query(CollectionSource).filter(
            CollectionSource.is_active == True
        ).all()

    def create_crawler(self, source: CollectionSource):
        """소스에 맞는 크롤러 생성"""
        config = self.CRAWLER_MAP.get(source.code)
        if not config:
            print(f"[!] Unknown source: {source.code}")
            return None

        crawler_type, target_id = config

        if crawler_type == 'naver_cafe':
            return NaverCafeCrawler(
                cafe_id=target_id,
                source_code=source.code,
                nid=self.naver_id,
                npw=self.naver_pw
            )
        elif crawler_type == 'dcinside':
            return DCInsideCrawler(
                gallery_id=target_id,
                source_code=source.code
            )

        return None

    async def crawl_source(
        self,
        source: CollectionSource,
        keyword: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """단일 소스 크롤링"""
        result = {
            'source_code': source.code,
            'success': False,
            'posts_collected': 0,
            'comments_collected': 0,
            'mentions_found': 0,
            'error': None
        }

        # 크롤링 로그 시작
        log = CrawlLog(
            source_id=source.id,
            started_at=datetime.utcnow(),
            status='running'
        )
        self.db.add(log)
        self.db.commit()

        try:
            crawler = self.create_crawler(source)
            if not crawler:
                raise Exception(f"Cannot create crawler for {source.code}")

            print(f"\n[*] Starting crawl: {source.name}")

            # 크롤링 실행
            if keyword:
                posts = await crawler.crawl(keyword=keyword, limit=limit)
            else:
                posts = await crawler.crawl_latest(limit=limit)

            print(f"[-] Crawled {len(posts)} posts")

            # 멘션 추출 및 저장
            stats = self.extractor.process_crawled_data(source, posts)

            result['success'] = True
            result['posts_collected'] = stats['posts_created'] + stats['posts_updated']
            result['comments_collected'] = stats['comments_created']
            result['mentions_found'] = stats['mentions_found']

            # 로그 업데이트
            log.status = 'completed'
            log.finished_at = datetime.utcnow()
            log.posts_collected = result['posts_collected']
            log.comments_collected = result['comments_collected']
            log.mentions_found = result['mentions_found']

        except Exception as e:
            result['error'] = str(e)
            print(f"[!] Crawl error: {e}")

            log.status = 'failed'
            log.finished_at = datetime.utcnow()
            log.error_message = str(e)

        self.db.commit()
        return result

    async def crawl_all_sources(
        self,
        keyword: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """모든 활성 소스 크롤링"""
        sources = self.get_active_sources()
        results = []

        print(f"\n{'='*50}")
        print(f"Starting crawl for {len(sources)} sources")
        print(f"Keyword: {keyword or '(latest)'}, Limit: {limit}")
        print(f"{'='*50}")

        for source in sources:
            result = await self.crawl_source(source, keyword, limit)
            results.append(result)

        # 요약 출력
        total_posts = sum(r['posts_collected'] for r in results)
        total_comments = sum(r['comments_collected'] for r in results)
        total_mentions = sum(r['mentions_found'] for r in results)
        success_count = sum(1 for r in results if r['success'])

        print(f"\n{'='*50}")
        print(f"Crawl Summary")
        print(f"{'='*50}")
        print(f"Sources: {success_count}/{len(sources)} successful")
        print(f"Posts: {total_posts}")
        print(f"Comments: {total_comments}")
        print(f"Mentions: {total_mentions}")

        return results

    async def crawl_by_teacher_names(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        강사 이름으로 검색하여 크롤링
        각 강사 이름을 키워드로 검색
        """
        from .models import Teacher

        teachers = self.db.query(Teacher).filter(Teacher.is_active == True).all()
        sources = self.get_active_sources()

        all_results = []

        print(f"\n{'='*50}")
        print(f"Crawling by teacher names")
        print(f"Teachers: {len(teachers)}, Sources: {len(sources)}")
        print(f"{'='*50}")

        for teacher in teachers[:10]:  # 테스트용 10명만
            print(f"\n[*] Searching for: {teacher.name}")

            for source in sources:
                try:
                    result = await self.crawl_source(source, keyword=teacher.name, limit=limit)
                    result['teacher_name'] = teacher.name
                    all_results.append(result)
                except Exception as e:
                    print(f"[!] Error: {e}")

                # 소스간 딜레이
                await asyncio.sleep(2)

            # 강사간 딜레이
            await asyncio.sleep(3)

        return all_results


async def run_daily_crawl(
    naver_id: str = None,
    naver_pw: str = None,
    limit: int = 50
):
    """데일리 크롤링 실행 함수"""
    db = SessionLocal()
    try:
        orchestrator = CrawlerOrchestrator(
            db=db,
            naver_id=naver_id,
            naver_pw=naver_pw
        )

        # 최신글 크롤링
        results = await orchestrator.crawl_all_sources(limit=limit)

        return results

    finally:
        db.close()


if __name__ == "__main__":
    import os

    naver_id = os.getenv("NAVER_ID")
    naver_pw = os.getenv("NAVER_PW")

    asyncio.run(run_daily_crawl(naver_id, naver_pw, limit=30))
