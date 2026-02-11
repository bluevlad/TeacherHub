"""
DC Inside Gallery Crawler
디시인사이드 갤러리 크롤러
"""
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from .base import BaseCrawler

logger = logging.getLogger(__name__)


class DCInsideCrawler(BaseCrawler):
    """디시인사이드 갤러리 크롤러"""

    # 갤러리 정보 (시드 데이터 기준)
    GALLERIES = {
        'government': {
            'name': '공무원 갤러리',
            'type': 'gallery',    # 일반 갤러리
            'url': 'https://gall.dcinside.com/board/lists/?id=government'
        },
        'gongmuwon': {
            'name': '공무원 마이너 갤러리',
            'type': 'mgallery',   # 마이너 갤러리
            'url': 'https://gall.dcinside.com/mgallery/board/lists/?id=gongmuwon'
        }
    }

    def __init__(self, gallery_id: str, source_code: str):
        """
        Args:
            gallery_id: 갤러리 ID (government, gongmuwon)
            source_code: 소스 코드 (DB 저장용)
        """
        gallery_info = self.GALLERIES.get(gallery_id, {})
        base_url = gallery_info.get('url', f'https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}')

        super().__init__(source_code, base_url)
        self.gallery_id = gallery_id
        self.gallery_type = gallery_info.get('type', 'mgallery')

    def _get_base_path(self) -> str:
        """갤러리 타입에 따른 기본 경로"""
        if self.gallery_type == 'gallery':
            return 'https://gall.dcinside.com/board'
        elif self.gallery_type == 'mini':
            return 'https://gall.dcinside.com/mini/board'
        return 'https://gall.dcinside.com/mgallery/board'

    async def crawl(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """키워드로 검색하여 크롤링"""
        results = []

        try:
            await self.setup_browser(headless=True, mobile=False)

            # 검색 URL 구성
            base_path = self._get_base_path()
            params = {
                'id': self.gallery_id,
                's_type': 'search_subject_memo',  # 제목+내용 검색
                's_keyword': keyword
            }
            search_url = f"{base_path}/lists/?{urlencode(params)}"
            logger.info(f"DC Inside Search: {search_url}")

            if not await self.safe_goto(search_url):
                return results

            # 목록 파싱
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')

            articles = self._parse_list_page(soup, limit)
            logger.info(f"Found {len(articles)} articles. Fetching details...")

            # 상세 페이지 크롤링
            for article in articles:
                detail = await self._crawl_detail(article['url'])
                article.update(detail)
                results.append(article)
                await self.random_delay(1000, 2000)

        finally:
            await self.close_browser()

        return results

    async def crawl_latest(self, limit: int = 50) -> List[Dict[str, Any]]:
        """최신글 크롤링"""
        results = []

        try:
            await self.setup_browser(headless=True, mobile=False)

            logger.info(f"DC Inside Latest: {self.base_url}")

            if not await self.safe_goto(self.base_url):
                return results

            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')

            articles = self._parse_list_page(soup, limit)
            logger.info(f"Found {len(articles)} articles. Fetching details...")

            for article in articles:
                detail = await self._crawl_detail(article['url'])
                article.update(detail)
                results.append(article)
                await self.random_delay(1000, 2000)

        finally:
            await self.close_browser()

        return results

    def _parse_list_page(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """목록 페이지 파싱"""
        articles = []

        # DC Inside 목록 테이블
        rows = soup.select("tr.ub-content")

        for row in rows[:limit]:
            try:
                article = self._parse_list_row(row)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.debug(f"Parse error: {e}")
                continue

        return articles

    def _parse_list_row(self, row) -> Optional[Dict[str, Any]]:
        """목록 행 파싱"""
        # 공지사항 제외
        if 'us-post' in row.get('class', []):
            return None

        # 게시글 번호
        num_elem = row.select_one("td.gall_num")
        if not num_elem:
            return None

        external_id = num_elem.get_text(strip=True)
        if not external_id.isdigit():  # 공지, 설문 등 제외
            return None

        # 제목
        title_elem = row.select_one("td.gall_tit a")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        href = title_elem.get('href', '')

        # URL 구성
        if href.startswith('/'):
            url = f"https://gall.dcinside.com{href}"
        else:
            url = href

        # 작성자
        author_elem = row.select_one("td.gall_writer")
        author = ''
        if author_elem:
            nick_elem = author_elem.select_one(".nickname")
            if nick_elem:
                author = nick_elem.get('title', '') or nick_elem.get_text(strip=True)

        # 날짜
        date_elem = row.select_one("td.gall_date")
        post_date = None
        if date_elem:
            date_str = date_elem.get('title', '') or date_elem.get_text(strip=True)
            post_date = self._parse_dc_date(date_str)

        # 조회수
        view_elem = row.select_one("td.gall_count")
        view_count = 0
        if view_elem:
            try:
                view_count = int(view_elem.get_text(strip=True).replace('-', '0'))
            except:
                pass

        # 추천수
        recommend_elem = row.select_one("td.gall_recommend")
        like_count = 0
        if recommend_elem:
            try:
                like_count = int(recommend_elem.get_text(strip=True).replace('-', '0'))
            except:
                pass

        # 댓글수 (제목 옆 [숫자])
        reply_elem = row.select_one("td.gall_tit .reply_num")
        comment_count = 0
        if reply_elem:
            reply_text = reply_elem.get_text(strip=True)
            match = re.search(r'\[(\d+)', reply_text)
            if match:
                comment_count = int(match.group(1))

        return {
            'external_id': external_id,
            'title': title,
            'url': url,
            'author': author,
            'post_date': post_date,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'content': '',
            'comments': []
        }

    def _parse_dc_date(self, date_str: str) -> Optional[datetime]:
        """DC인사이드 날짜 파싱"""
        if not date_str:
            return None

        try:
            # YYYY-MM-DD HH:MM:SS 형식
            if len(date_str) >= 19:
                return datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
            # YYYY-MM-DD 형식
            elif len(date_str) >= 10:
                return datetime.strptime(date_str[:10], "%Y-%m-%d")
            # HH:MM 형식 (오늘)
            elif ':' in date_str and len(date_str) <= 5:
                now = datetime.now()
                parts = date_str.split(':')
                return now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0, microsecond=0)
            # MM.DD 형식
            elif '.' in date_str and len(date_str) <= 5:
                now = datetime.now()
                parts = date_str.split('.')
                return now.replace(month=int(parts[0]), day=int(parts[1]))
        except Exception as e:
            logger.debug(f"DC date parse error: {date_str} - {e}")

        return None

    async def _crawl_detail(self, url: str) -> Dict[str, Any]:
        """상세 페이지 크롤링"""
        result = {
            'content': '',
            'comments': []
        }

        try:
            await self.safe_goto(url)
            await self.page.wait_for_timeout(1500)

            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # 본문 추출
            content_elem = soup.select_one(".write_div")
            if content_elem:
                # 이미지, 동영상 태그 제거하고 텍스트만
                for tag in content_elem.select('img, video, iframe, script, style'):
                    tag.decompose()
                result['content'] = content_elem.get_text(strip=True)

            # 댓글 추출
            comments = []
            comment_list = soup.select(".cmt_info")

            for idx, cmt in enumerate(comment_list):
                try:
                    content_elem = cmt.select_one(".usertxt")
                    author_elem = cmt.select_one(".gall_writer .nickname")
                    date_elem = cmt.select_one(".date_time")

                    if content_elem:
                        comments.append({
                            'external_id': str(idx),
                            'content': content_elem.get_text(strip=True),
                            'author': author_elem.get('title', '') if author_elem else '',
                            'comment_date': self._parse_dc_date(date_elem.get_text(strip=True) if date_elem else None),
                            'like_count': 0
                        })
                except Exception as e:
                    continue

            result['comments'] = comments

        except Exception as e:
            logger.warning(f"Detail crawl error: {e}")

        return result
