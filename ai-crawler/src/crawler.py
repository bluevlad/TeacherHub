import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
import random

class NaverCafeCrawler:
    def __init__(self, cafe_url, keyword, nid=None, npw=None):
        self.cafe_url = cafe_url
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
        print("[-] Login interaction done. (Check manually if captcha triggered)")

    async def crawl(self, limit=5):
        print(f"[*] Starting crawl for: {self.cafe_url} with keyword: {self.keyword}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # 0. Login if needed
            if self.nid and self.npw:
                await self.login(page)
            
            # 1. Access Cafe Main Page
            await page.goto(self.cafe_url)
            await page.wait_for_load_state("networkidle")
            
            # 2. Search Logic
            # Note: Naver Cafe structure is complex with iframes.
            # We will try to find the search input 'query' in the main frame or top frame.
            try:
                # Common selector for cafe search input
                await page.fill("input[name='query']", self.keyword)
                await page.press("input[name='query']", "Enter")
                print("[-] Search query submitted.")
            except Exception as e:
                print(f"[!] Search input not found directly. Trying alternative approach. Error: {e}")
                # Alternative: constructing search URL if we knew clubid.
                # For this sample, we assume standard layout.
                return []

            await page.wait_for_timeout(2000) # Wait for iframe reload

            # 3. Switch to 'cafe_main' iframe where content lives
            try:
                # Wait for the iframe to be attached
                frame_element = await page.wait_for_selector("iframe#cafe_main")
                frame = await frame_element.content_frame()
                await frame.wait_for_selector(".article-board", timeout=5000)
            except:
                print("[!] Could not find content frame or board.")
                return []
            
            # 4. Parse List
            content = await frame.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract article links
            articles = []
            rows = soup.select(".article-board table tbody tr")
            
            for row in rows:
                try:
                    title_elem = row.select_one(".article")
                    if not title_elem: continue
                    
                    title = title_elem.get_text(strip=True)
                    link = "https://cafe.naver.com" + title_elem['href']
                    article_id = title_elem['href'].split('articleid=')[1].split('&')[0]
                    
                    articles.append({
                        'id': article_id,
                        'title': title,
                        'link': link
                    })
                    if len(articles) >= limit: break
                except:
                    continue
            
            print(f"[-] Found {len(articles)} articles. Starting details crawl...")

            # 5. Detail Crawl
            final_data = []
            for art in articles:
                print(f"    -> Visiting: {art['title'][:20]}...")
                try:
                    # Visit article url. Note: Naver Cafe articles often require switching frame again if visited directly
                    # Trick: Mobile URL is easier: https://m.cafe.naver.com/...
                    # Let's try visiting the link directly and handling iframe
                    await page.goto(art['link'])
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(1000)
                    
                    # Again, content is inside iframe#cafe_main
                    frame_element = await page.wait_for_selector("iframe#cafe_main")
                    frame = await frame_element.content_frame()
                    
                    # Get Content
                    content_html = await frame.content()
                    detail_soup = BeautifulSoup(content_html, 'html.parser')
                    
                    # Title
                    real_title = detail_soup.select_one(".title_text").get_text(strip=True) if detail_soup.select_one(".title_text") else art['title']
                    
                    # Content
                    body_text = ""
                    content_container = detail_soup.select_one(".ContentRenderer") # Class name varies often: se-main-container, etc.
                    if content_container:
                        body_text = content_container.get_text(strip=True)
                    else:
                        # Fallback for old editor
                        content_container = detail_soup.select_one("#tbody")
                        if content_container: body_text = content_container.get_text(strip=True)

                    # Comments
                    comments = []
                    # Comments are often dynamic. Wait for comment section
                    # Handling comment collection is complex due to AJAX. 
                    # For sample, we try to grab rendered text if available immediately.
                    comment_elems = detail_soup.select(".comment_text_box")
                    for c in comment_elems:
                        comments.append(c.get_text(strip=True))

                    final_data.append({
                        'title': real_title,
                        'content': body_text[:200] + "..." if len(body_text) > 200 else body_text,
                        'comments': comments,
                        'url': art['link']
                    })
                    
                    # Polite delay
                    await page.wait_for_timeout(random.randint(1000, 2000))
                    
                except Exception as e:
                    print(f"[!] Error processing article {art['link']}: {e}")
                    continue

            await browser.close()
            return final_data
