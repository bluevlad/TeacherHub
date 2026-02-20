"""
Naver Cafe Crawler
네이버 카페 크롤러
"""
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from .base import BaseCrawler

logger = logging.getLogger(__name__)


class NaverCafeCrawler(BaseCrawler):
    """네이버 카페 크롤러"""

    # 카페별 Club ID 매핑 (자동 감지 실패 시 사용)
    CAFE_IDS = {
        'gongstar': '28956533',      # 공스타그램
        'm2school': '12026840',      # 공드림 (독공사)
        '9gong': '16558386',         # 9급공무원갤러리
    }

    def __init__(self, cafe_id: str, source_code: str, nid: str = None, npw: str = None):
        """
        Args:
            cafe_id: 카페 ID (예: gongstar, m2school)
            source_code: 소스 코드 (DB 저장용)
            nid: 네이버 아이디 (로그인 필요 시)
            npw: 네이버 비밀번호
        """
        super().__init__(source_code, f"https://m.cafe.naver.com/{cafe_id}")
        self.cafe_id = cafe_id
        self.nid = nid
        self.npw = npw
        self.club_id = self.CAFE_IDS.get(cafe_id)

    async def login(self):
        """네이버 로그인"""
        if not self.nid or not self.npw:
            logger.info("No credentials provided. Skipping login.")
            return False

        logger.info("Attempting Naver login...")
        try:
            await self.page.goto("https://nid.naver.com/nidlogin.login")
            await self.page.fill('#id', self.nid)
            await self.page.fill('#pw', self.npw)
            await self.random_delay(800, 1200)
            await self.page.click(".btn_login")
            await self.page.wait_for_load_state("networkidle")
            logger.info("Login completed.")
            return True
        except Exception as e:
            logger.warning(f"Login failed: {e}")
            return False

    async def get_club_id(self) -> Optional[str]:
        """카페 Club ID 추출"""
        if self.club_id:
            return self.club_id

        try:
            await self.safe_goto(self.base_url)
            element = await self.page.query_selector("a[href*='clubid=']")
            if element:
                href = await element.get_attribute("href")
                match = re.search(r'clubid=(\d+)', href)
                if match:
                    self.club_id = match.group(1)
                    logger.info(f"Detected ClubID: {self.club_id}")
                    return self.club_id
        except Exception as e:
            logger.error(f"Failed to get club ID: {e}")

        return None

    async def crawl(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """키워드로 검색하여 크롤링"""
        results = []

        try:
            await self.setup_browser(headless=True, mobile=True)

            if self.nid and self.npw:
                login_ok = await self.login()
                if not login_ok:
                    logger.info("Continuing without login (fallback)")

            club_id = await self.get_club_id()
            if not club_id:
                logger.error("Failed to get ClubID. Aborting.")
                return results

            # 검색 URL
            search_url = f"https://m.cafe.naver.com/SectionArticleSearch.nhn?clubid={club_id}&query={keyword}&sortBy=date"
            logger.info(f"Crawling: {search_url}")

            if not await self.safe_goto(search_url):
                return results

            # 목록 셀렉터 대기 (여러 셀렉터 시도)
            list_selectors = ["ul.list_area", "ul.article-list", "div.ArticleSearchListArea"]
            list_found = False
            for sel in list_selectors:
                try:
                    await self.page.wait_for_selector(sel, timeout=5000)
                    list_found = True
                    break
                except:
                    continue

            if not list_found:
                logger.warning("No results found")
                return results

            # 목록 파싱
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            items = soup.select("ul.list_area > li")
            if not items:
                items = soup.select("ul.article-list > li")

            articles = []
            for item in items[:limit]:
                try:
                    article = self._parse_list_item(item)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.debug(f"Parse error: {e}")
                    continue

            logger.info(f"Found {len(articles)} articles. Fetching details...")

            # 상세 페이지 크롤링
            for article in articles:
                detail = await self._crawl_detail(article['url'])
                article.update(detail)
                results.append(article)
                await self.random_delay()

        finally:
            await self.close_browser()

        return results

    async def crawl_latest(self, limit: int = 50) -> List[Dict[str, Any]]:
        """최신글 크롤링 (전체 게시판)"""
        results = []

        try:
            await self.setup_browser(headless=True, mobile=True)

            if self.nid and self.npw:
                login_ok = await self.login()
                if not login_ok:
                    logger.info("Continuing without login (fallback)")

            club_id = await self.get_club_id()
            if not club_id:
                return results

            # 전체글 보기 URL
            list_url = f"https://m.cafe.naver.com/ArticleList.nhn?search.clubid={club_id}&search.menuid=0&search.boardtype=L"
            logger.info(f"Crawling latest: {list_url}")

            if not await self.safe_goto(list_url):
                return results

            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            items = soup.select("ul.list_area > li")
            if not items:
                items = soup.select("ul.article-list > li")

            for item in items[:limit]:
                try:
                    article = self._parse_list_item(item)
                    if article:
                        detail = await self._crawl_detail(article['url'])
                        article.update(detail)
                        results.append(article)
                        await self.random_delay()
                except Exception as e:
                    logger.debug(f"Error: {e}")
                    continue

        finally:
            await self.close_browser()

        return results

    def _parse_list_item(self, item) -> Optional[Dict[str, Any]]:
        """목록 아이템 파싱"""
        title_elem = item.select_one(".tit")
        if not title_elem:
            return None

        link_elem = item.select_one("a.txt_area")
        if not link_elem:
            return None

        href = link_elem.get('href', '')
        # external_id 추출
        match = re.search(r'articleid=(\d+)', href)
        external_id = match.group(1) if match else None

        date_elem = item.select_one(".time")
        comment_elem = item.select_one(".num")

        return {
            'external_id': external_id,
            'title': title_elem.get_text(strip=True),
            'url': f"https://m.cafe.naver.com{href}" if href.startswith('/') else href,
            'post_date': self.parse_date(date_elem.get_text(strip=True) if date_elem else None),
            'comment_count': int(comment_elem.get_text(strip=True)) if comment_elem else 0,
            'content': '',
            'author': '',
            'view_count': 0,
            'like_count': 0,
            'comments': []
        }

    async def _crawl_detail(self, url: str) -> Dict[str, Any]:
        """상세 페이지 크롤링"""
        result = {
            'content': '',
            'author': '',
            'view_count': 0,
            'like_count': 0,
            'comments': []
        }

        try:
            await self.safe_goto(url)
            await self.page.wait_for_timeout(1000)

            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # 본문 추출
            content_selectors = ["#postContent", ".se-main-container", ".post_content", "div.ContentRenderer"]
            for sel in content_selectors:
                elem = soup.select_one(sel)
                if elem:
                    result['content'] = elem.get_text(strip=True)
                    break

            # 작성자
            author_elem = soup.select_one(".nick") or soup.select_one(".writer")
            if author_elem:
                result['author'] = author_elem.get_text(strip=True)

            # 조회수
            view_elem = soup.select_one(".no")
            if view_elem:
                try:
                    result['view_count'] = int(re.sub(r'[^\d]', '', view_elem.get_text()))
                except:
                    pass

            # 댓글 추출
            comments = []
            comment_items = soup.select(".u_cbox_comment_box")
            for idx, c_item in enumerate(comment_items):
                content_elem = c_item.select_one(".u_cbox_contents")
                author_elem = c_item.select_one(".u_cbox_nick")
                date_elem = c_item.select_one(".u_cbox_date")

                if content_elem:
                    comments.append({
                        'external_id': str(idx),
                        'content': content_elem.get_text(strip=True),
                        'author': author_elem.get_text(strip=True) if author_elem else '',
                        'comment_date': self.parse_date(date_elem.get_text(strip=True) if date_elem else None),
                        'like_count': 0
                    })

            result['comments'] = comments
            if len(comments) > result.get('comment_count', 0):
                result['comment_count'] = len(comments)

        except Exception as e:
            logger.warning(f"Detail crawl error: {e}")

        return result
