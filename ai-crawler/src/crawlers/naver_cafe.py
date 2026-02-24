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
        'gongstar': '30507866',      # 공스타그램
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
        super().__init__(source_code, f"https://cafe.naver.com/{cafe_id}")
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
        """키워드로 검색하여 크롤링 (데스크톱 모드)"""
        results = []

        try:
            await self.setup_browser(headless=True, mobile=False)

            if self.nid and self.npw:
                login_ok = await self.login()
                if not login_ok:
                    logger.info("Continuing without login (fallback)")

            club_id = await self.get_club_id()
            if not club_id:
                logger.error("Failed to get ClubID. Aborting.")
                return results

            # 데스크톱 검색 URL
            search_url = f"https://cafe.naver.com/ArticleSearchList.nhn?search.clubid={club_id}&search.searchBy=1&search.query={keyword}&search.sortBy=date"
            logger.info(f"Crawling: {search_url}")

            if not await self.safe_goto(search_url):
                return results

            # 목록 셀렉터 대기 (데스크톱)
            list_selectors = ["a.article", "table.board-list", ".article-board"]
            list_found = False
            for sel in list_selectors:
                try:
                    await self.page.wait_for_selector(sel, timeout=5000)
                    list_found = True
                    break
                except Exception:
                    continue

            if not list_found:
                logger.warning("No results found")
                return results

            # 목록 파싱 (데스크톱)
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            items = soup.select("a.article")

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
        """최신글 크롤링 (전체 게시판, 데스크톱 모드)"""
        results = []

        try:
            await self.setup_browser(headless=True, mobile=False)

            if self.nid and self.npw:
                login_ok = await self.login()
                if not login_ok:
                    logger.info("Continuing without login (fallback)")

            club_id = await self.get_club_id()
            if not club_id:
                return results

            # 데스크톱 전체글 보기 URL
            list_url = f"https://cafe.naver.com/ArticleList.nhn?search.clubid={club_id}&search.menuid=0&search.boardtype=L"
            logger.info(f"Crawling latest: {list_url}")

            if not await self.safe_goto(list_url):
                return results

            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            items = soup.select("a.article")

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
        """목록 아이템 파싱 (데스크톱 모드: item은 a.article 엘리먼트)"""
        href = item.get('href', '')
        if not href:
            return None

        # external_id 추출 (새 URL: /articles/12345, 구 URL: articleid=12345)
        match = re.search(r'/articles/(\d+)', href) or re.search(r'articleid=(\d+)', href)
        external_id = match.group(1) if match else None
        if not external_id:
            return None

        # 제목 추출 (a.article 내부 텍스트)
        title = item.get_text(strip=True)
        if not title:
            return None

        # 부모 행(tr)에서 추가 정보 추출
        row = item.find_parent('tr')
        date_str = ''
        view_count = 0
        comment_count = 0
        author = ''

        if row:
            # 날짜 (td.type_date)
            date_elem = row.select_one('.type_date')
            if date_elem:
                date_str = date_elem.get_text(strip=True)

            # 조회수 (td.type_readCount)
            view_elem = row.select_one('.type_readCount')
            if view_elem:
                try:
                    view_count = int(re.sub(r'[^\d]', '', view_elem.get_text()))
                except (ValueError, TypeError):
                    pass

            # 작성자 (.nickname)
            nick_elem = row.select_one('.nickname')
            if nick_elem:
                author = nick_elem.get_text(strip=True)

            # 댓글수 (a.cmt 내부 [숫자])
            cmt_elem = row.select_one('a.cmt')
            if cmt_elem:
                cmt_text = cmt_elem.get_text(strip=True)
                cmt_match = re.search(r'\[(\d+)\]', cmt_text)
                if cmt_match:
                    comment_count = int(cmt_match.group(1))

        # URL (이미 절대경로)
        if href.startswith('/'):
            url = f"https://cafe.naver.com{href}"
        else:
            url = href

        return {
            'external_id': external_id,
            'title': title,
            'url': url,
            'post_date': self.parse_date(date_str),
            'comment_count': comment_count,
            'content': '',
            'author': author,
            'view_count': view_count,
            'like_count': 0,
            'comments': []
        }

    async def _crawl_detail(self, url: str) -> Dict[str, Any]:
        """상세 페이지 크롤링 (데스크톱 모드)"""
        result = {
            'content': '',
            'author': '',
            'view_count': 0,
            'like_count': 0,
            'comments': []
        }

        try:
            # 데스크톱 URL로 변환 (m.cafe → cafe)
            desktop_url = url.replace("m.cafe.naver.com", "cafe.naver.com")
            await self.safe_goto(desktop_url)
            await self.page.wait_for_timeout(1500)

            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # 본문 추출 (데스크톱 + 모바일 셀렉터 모두 시도)
            content_selectors = [
                ".se-main-container", "#postContent", ".post_content",
                "div.ContentRenderer", ".article_viewer", "#body"
            ]
            for sel in content_selectors:
                elem = soup.select_one(sel)
                if elem:
                    result['content'] = elem.get_text(strip=True)
                    break

            # 작성자 (데스크톱 셀렉터)
            author_selectors = [
                ".WriterInfo .nickname", ".article_writer .nickname",
                ".nick_box .nickname", ".nick", ".writer"
            ]
            for sel in author_selectors:
                author_elem = soup.select_one(sel)
                if author_elem:
                    result['author'] = author_elem.get_text(strip=True)
                    break

            # 조회수 (데스크톱 셀렉터)
            view_selectors = [
                ".article_info .count", ".no", ".view_count",
                "span.count"
            ]
            for sel in view_selectors:
                view_elem = soup.select_one(sel)
                if view_elem:
                    try:
                        result['view_count'] = int(re.sub(r'[^\d]', '', view_elem.get_text()))
                        break
                    except (ValueError, TypeError):
                        continue

            # 댓글 추출 (u_cbox는 데스크톱/모바일 공통)
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
