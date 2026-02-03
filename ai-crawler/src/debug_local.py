import asyncio
import os
import sys

# Force UTF-8 for Windows Terminal
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from crawler import NaverCafeCrawler
from analyzer import SentimentAnalyzer
from datetime import datetime

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Database Connection (Localhost)
DB_USER = os.getenv("DB_USER", "teacher")
DB_PASS = os.getenv("DB_PASS", "password")
DB_HOST = "localhost" # Force localhost for local access
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "teacherhub")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("[+] DB Connection Successful!")
except Exception as e:
    print(f"[!] DB Connection Failed: {e}")
    print("Ensure Docker DB is running and accessible on port 5432.")
    # We might continue just to test crawling even if DB fails
    # sys.exit(1)

def save_to_db(data):
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO reputation_data (keyword, site_name, title, url, sentiment, score, post_date, comment_count)
                VALUES (:keyword, :site_name, :title, :url, :sentiment, :score, :post_date, :comment_count)
            """)
            conn.execute(query, data)
            conn.commit()
            print(f"    [DB] Saved: {data['title'][:20]}...")
    except Exception as e:
        print(f"    [DB Error] {e}")

async def run_debug():
    # Force Headless=False for debugging
    # We need to monkey-patch or subclass, OR just modify crawler.py to accept headless arg.
    # Let's modify crawler.py to accept headless arg first.
    
    TARGET_URL = "https://cafe.naver.com/m2school"
    SITE_NAME = "Naver Cafe (GongDream)"
    KEYWORD = "윌비스"
    NAVER_ID = os.getenv("NAVER_ID")
    NAVER_PW = os.getenv("NAVER_PW")

    print(f"[*] Crawling '{KEYWORD}' with ID: {NAVER_ID}")

    # We need to modify crawler.py to allow passing headless option.
    # checking crawler.py... it has `browser = await p.chromium.launch(headless=True)` hardcoded.
    # I'll update crawler.py first.

    crawler = NaverCafeCrawler(TARGET_URL, KEYWORD, nid=NAVER_ID, npw=NAVER_PW)
    # Pass headless=False if supported
    posts = await crawler.crawl(limit=50, start_date='2025-10-01', end_date='2025-12-31', headless=False)
    
    if not posts:
        print("[!] No posts found.")
        return

    analyzer = SentimentAnalyzer()
    print(f"\n[-] Analysis & Saving ({len(posts)} posts):")
    
    for post in posts:
        full_text = f"{post['title']} {post['content']} {' '.join(post['comments'])}"
        result = analyzer.analyze(full_text)
        
        # Date Filter Logic (Same as main.py)
        p_date_str = post.get('post_date_str', '')
        post_date = datetime.now()
        try:
            p_date_str = p_date_str.replace('.', '-').strip()
            if p_date_str.endswith('-'): p_date_str = p_date_str[:-1]
            if ':' in p_date_str and len(p_date_str) <= 5:
                now = datetime.now()
                hm = p_date_str.split(':')
                post_date = now.replace(hour=int(hm[0]), minute=int(hm[1]), second=0)
            elif len(p_date_str) == 8:
                 post_date = datetime.strptime(p_date_str, "%y-%m-%d")
            elif len(p_date_str) >= 10:
                 post_date = datetime.strptime(p_date_str, "%Y-%m-%d")
            
            target_start = datetime(2025, 10, 1)
            target_end = datetime(2025, 12, 31, 23, 59, 59)
            if not (target_start <= post_date <= target_end):
                print(f"    [Skipped] Date out of range: {post_date}")
                continue
        except:
             pass

        db_data = {
            "keyword": KEYWORD,
            "site_name": SITE_NAME,
            "title": post['title'],
            "url": post['url'],
            "sentiment": result['label'],
            "score": result['score'],
            "post_date": post_date,
            "comment_count": post.get('comment_count', 0)
        }
        save_to_db(db_data)

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        # On Windows, the default event loop policy (ProactorEventLoop) doesn't support subprocesses well with some async frameworks.
        # However, Playwright on Windows usually requires ProactorEventLoop for subprocess pipes?
        # WAIT: The error "NotImplementedError" in subprocess_exec usuall means using SelectorEventLoop on Windows which DOES NOT support subprocesses.
        # The default on Python 3.8+ Windows IS ProactorEventLoop, which supports subprocesses.
        # But `asyncio.WindowsSelectorEventLoopPolicy()` explicitly sets it to Selector, causing failure.
        # Therefore, we should REMOVE the policy setting or force Proactor.
        # The common fix for "NotImplementedError" in asyncio subprocess on Windows is usually to USE Proactor (default).
        # So the previous code setting SelectorEventLoopPolicy was actually the CAUSE of the error.
        # Let's remove it.
        pass
    
    asyncio.run(run_debug())
