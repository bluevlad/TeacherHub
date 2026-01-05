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

    async def crawl(self, limit=10):
        search_url = f"{self.mobile_base}/search?search.query={self.keyword}&search.sortBy=date&search.option=all"
        print(f"[*] Starting Mobile crawl for: {search_url}")
        
        # Mobile User Agent
        MOBILE_UA = "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=MOBILE_UA,
                viewport={"width": 375, "height": 812}
            )
            page = await context.new_page()
            
            # 0. Login if needed
            if self.nid and self.npw:
                await self.login(page)
            
            # 1. Access Search Page Directly
            try:
                await page.goto(search_url)
                await page.wait_for_load_state("networkidle")
                await page.wait_for_selector("ul.list_area", timeout=10000) # Wait for list
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
