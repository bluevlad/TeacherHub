import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
import random

class NaverCafeCrawler:
    def __init__(self, cafe_url, keyword, nid=None, npw=None):
        # Determine Mobile URL
        # cafe_url input: https://cafe.naver.com/m2school
        # mobile url target: https://m.cafe.naver.com/m2school
        self.cafe_id = cafe_url.split('/')[-1]
        self.mobile_base = f"https://m.cafe.naver.com/{self.cafe_id}"
        self.keyword = keyword
        self.nid = nid
        self.npw = npw
        self.results = []

    async def login(self, page):
        if not self.nid or not self.npw:
            print("[-] No credentials provided. Skipping login.")
            return

        print("[-] Attempting login...")
        await page.goto("https://nid.naver.com/nidlogin.login")
        
        # Clipbaord copy-paste method to bypass simple bot detection
        await page.evaluate(f"document.getElementById('id').value = '{self.nid}'")
        await page.evaluate(f"document.getElementById('pw').value = '{self.npw}'")
        
        await page.wait_for_timeout(1000)
        # Click login button
        await page.click(".btn_login")
        await page.wait_for_load_state("networkidle")
        print("[-] Login interaction done.")

    async def crawl(self, limit=50, start_date=None, end_date=None, headless=True):
        # Mobile search basic
        # We will fetch 'limit' items sorted by date, and filter by date range later if provided
        search_url = f"{self.mobile_base}/search?search.query={self.keyword}&search.sortBy=date&search.option=all"
        print(f"[*] Starting Mobile crawl for: {search_url}")
        
        # Update User Agent to a more common real device UA
        MOBILE_UA = "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36"

        async with async_playwright() as p:
            # Add arguments to launch options for better stealth
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            
            context = await browser.new_context(
                user_agent=MOBILE_UA,
                viewport={"width": 375, "height": 812},
                base_url="https://m.cafe.naver.com",
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                extra_http_headers={
                    "Referer": "https://m.cafe.naver.com/",
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
                }
            )
            
            # Stealth scripts to hide webdriver property
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = await context.new_page()
            
            # 0. Login if needed
            if self.nid and self.npw:
                await self.login(page)
            
            # 1. Get Club ID first (Robust way)
            clubid = None
            try:
                print(f"[-] Fetching Club ID from: {self.mobile_base}")
                await page.goto(self.mobile_base, wait_until="domcontentloaded")
                
                # Try to find clubid in links or script
                # Common pattern: href contains "clubid=12345"
                # Let's verify via any article link or specific meta
                # Or use the user hint directly if extraction fails, but extraction is better.
                
                # Check for "g_iClubId" javaScript variable if possible, or look at hrefs
                if not clubid:
                    # Method A: Look for any link with clubid
                    element = await page.query_selector("a[href*='clubid=']")
                    if element:
                        href = await element.get_attribute("href")
                        # Extract 12026840 from ...clubid=12026840...
                        import re
                        match = re.search(r'clubid=(\d+)', href)
                        if match:
                            clubid = match.group(1)
            except Exception as e:
                print(f"[!] Warning: Failed to extract clubid automatically: {e}")

            if not clubid:
                # Fallback to hardcoded ID for 'm2school' (Dokgongsa) if detection failed
                # User provided: 12026840
                if 'm2school' in self.cafe_id:
                     clubid = "12026840" 
                     print(f"[-] Using fallback ClubID: {clubid}")
                else:
                     print("[!] Failed to determine ClubID. Aborting.")
                     await browser.close()
                     return []
            else:
                print(f"[-] Detected ClubID: {clubid}")

            # 2. Access Search Page (SectionArticleSearch)
            # Old/Standard Mobile Search: https://m.cafe.naver.com/SectionArticleSearch.nhn?clubid={}&query={}&sortBy=date
            search_url = f"https://m.cafe.naver.com/SectionArticleSearch.nhn?clubid={clubid}&query={self.keyword}&sortBy=date"
            print(f"[*] Starting Mobile crawl for: {search_url}")

            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                await page.wait_for_selector("ul.list_area", timeout=10000)
            except Exception as e:
                print(f"[!] Init Failed: {e}")
                await browser.close()
                return []

            # 2. Parse List
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            articles = []
            # Mobile list selector
            items = soup.select("ul.list_area > li")
            
            for item in items:
                try:
                    title_elem = item.select_one(".tit")
                    if not title_elem: continue
                    
                    title = title_elem.get_text(strip=True)
                    # Link is usually in a parent or sibling anchor
                    link_elem = item.select_one("a.txt_area")
                    if not link_elem: continue
                    
                    href = link_elem['href']
                    # href format: /ArticleRead.nhn?clubid=...&articleid=...
                    link = f"https://m.cafe.naver.com{href}"
                    
                    # Date & Comments
                    date_elem = item.select_one(".time")
                    post_date_str = date_elem.get_text(strip=True) if date_elem else ""
                    
                    comment_elem = item.select_one(".num") # Class 'num' usually contains comment count
                    comment_count = 0
                    if comment_elem:
                        try:
                            comment_count = int(comment_elem.get_text(strip=True))
                        except: pass

                    articles.append({
                        'title': title,
                        'link': link,
                        'post_date_str': post_date_str,
                        'comment_count': comment_count,
                        'comments': [] # Will fill later
                    })
                    if len(articles) >= limit: break
                except Exception as ex:
                    print(f"[!] Parse error: {ex}")
                    continue
            
            print(f"[-] Found {len(articles)} articles. Starting details crawl...")

            # 3. Detail Crawl (for content and comments)
            for art in articles:
                print(f"    -> Visiting: {art['title'][:20]}...")
                try:
                    await page.goto(art['link'])
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(1000)
                    
                    detail_html = await page.content()
                    d_soup = BeautifulSoup(detail_html, 'html.parser')
                    
                    # Content (Mobile)
                    # Usually #postContent or .post_content or .se-main-container
                    content_body = ""
                    # Try common mobile selectors
                    selectors = ["#postContent", ".se-main-container", ".post_content", "div.ContentRenderer"]
                    for sel in selectors:
                        c_elem = d_soup.select_one(sel)
                        if c_elem:
                            content_body = c_elem.get_text(strip=True)
                            break
                    
                    # Comments
                    # Mobile comments are usually .u_cbox_contents or similar.
                    # Sometimes comments are loaded via AJAX and might need wait.
                    # We will try static parse first.
                    comments = []
                    c_items = d_soup.select(".u_cbox_contents")
                    for c in c_items:
                        comments.append(c.get_text(strip=True))
                        
                    art['content'] = content_body[:300]
                    art['comments'] = comments
                    # Update comment count if we found more actual comments
                    if len(comments) > art['comment_count']:
                        art['comment_count'] = len(comments)

                    await page.wait_for_timeout(random.randint(500, 1500))

                except Exception as e:
                    print(f"[!] Error details {art['link']}: {e}")
                    art['content'] = ""
                    continue

            await browser.close()
            return articles
