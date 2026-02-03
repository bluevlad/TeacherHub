"""
Base Crawler Class
공통 크롤링 기능 추상화
"""
import asyncio
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BaseCrawler(ABC):
    """크롤러 기본 클래스"""

    # User Agents
    DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    MOBILE_UA = "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36"

    def __init__(self, source_code: str, base_url: str):
        self.source_code = source_code
        self.base_url = base_url
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def setup_browser(self, headless: bool = True, mobile: bool = False) -> Page:
        """브라우저 설정 및 페이지 반환"""
        playwright = await async_playwright().start()

        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        ua = self.MOBILE_UA if mobile else self.DESKTOP_UA
        viewport = {"width": 375, "height": 812} if mobile else {"width": 1920, "height": 1080}

        self.context = await self.browser.new_context(
            user_agent=ua,
            viewport=viewport,
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            extra_http_headers={
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            }
        )

        # Stealth 설정
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """)

        self.page = await self.context.new_page()
        return self.page

    async def close_browser(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None

    async def random_delay(self, min_ms: int = 500, max_ms: int = 1500):
        """랜덤 딜레이"""
        await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)

    async def safe_goto(self, url: str, timeout: int = 30000) -> bool:
        """안전한 페이지 이동"""
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            await self.random_delay(1000, 2000)
            return True
        except Exception as e:
            print(f"[!] Navigation failed: {url} - {e}")
            return False

    @abstractmethod
    async def crawl(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        크롤링 실행 (하위 클래스에서 구현)

        Returns:
            List of dict with keys:
            - external_id: str
            - title: str
            - content: str
            - url: str
            - author: str
            - post_date: datetime
            - view_count: int
            - like_count: int
            - comment_count: int
            - comments: List[dict] with keys: external_id, content, author, comment_date
        """
        pass

    @abstractmethod
    async def crawl_latest(self, limit: int = 50) -> List[Dict[str, Any]]:
        """최신글 크롤링 (키워드 없이)"""
        pass

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱 (공통 로직)"""
        if not date_str:
            return None

        date_str = date_str.strip()
        now = datetime.now()

        try:
            # 오늘 시간만 있는 경우 (HH:MM)
            if ':' in date_str and len(date_str) <= 5:
                parts = date_str.split(':')
                return now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0, microsecond=0)

            # YY.MM.DD 형식
            date_str = date_str.replace('.', '-').replace('/', '-')
            if date_str.endswith('-'):
                date_str = date_str[:-1]

            if len(date_str) == 8:  # YY-MM-DD
                return datetime.strptime(date_str, "%y-%m-%d")
            elif len(date_str) >= 10:  # YYYY-MM-DD
                return datetime.strptime(date_str[:10], "%Y-%m-%d")

        except Exception as e:
            print(f"[!] Date parse error: {date_str} - {e}")

        return None
