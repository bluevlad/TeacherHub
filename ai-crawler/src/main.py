import asyncio
import time
import os
from sqlalchemy import create_engine, text
from crawler import NaverCafeCrawler
from analyzer import SentimentAnalyzer

# Database Connection
DB_USER = os.getenv("DB_USER", "teacher")
DB_PASS = os.getenv("DB_PASS", "password")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "teacherhub")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

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

async def run_task():
    TARGET_URL = "https://cafe.naver.com/m2school"
    SITE_NAME = "Naver Cafe (GongDream)"
    KEYWORD = "한덕현"
    
    # Creds
    NAVER_ID = os.getenv("NAVER_ID")
    NAVER_PW = os.getenv("NAVER_PW")
    
    print("-" * 50)
    print(f"TeacherHub AI Crawler Sample Start")
    if NAVER_ID:
        print(f"[*] Login mode enabled for user: {NAVER_ID[:3]}***")
    print("-" * 50)

    # 1. Crawl
    crawler = NaverCafeCrawler(TARGET_URL, KEYWORD, nid=NAVER_ID, npw=NAVER_PW)
    posts = await crawler.crawl(limit=5)
    
    if not posts:
        print("[!] No posts found.")
        return

    # 2. Analyze & Save
    analyzer = SentimentAnalyzer()
    
    print(f"\n[-] Analysis & Saving ({len(posts)} posts):")
    from datetime import datetime, timedelta
    
    for post in posts:
        full_text = f"{post['title']} {post['content']} {' '.join(post['comments'])}"
        result = analyzer.analyze(full_text)
        
        # Parse Date
        # post_date_str format: 
        # PC: "2024.01.05." or "14:22"
        # Mobile: "24.01.05." or "14:22" (Year is 2 digits)
        p_date_str = post.get('post_date_str', '')
        post_date = datetime.now() # Default
        
        try:
            p_date_str = p_date_str.replace('.', '-').strip()
            if p_date_str.endswith('-'): p_date_str = p_date_str[:-1]
            
            if ':' in p_date_str and len(p_date_str) <= 5: # HH:mm (Today)
                # It is today's time
                now = datetime.now()
                hm = p_date_str.split(':')
                post_date = now.replace(hour=int(hm[0]), minute=int(hm[1]), second=0)
            elif len(p_date_str) == 8: # YY-MM-DD (e.g., 24-01-05)
                 post_date = datetime.strptime(p_date_str, "%y-%m-%d")
            elif len(p_date_str) >= 10: # YYYY-MM-DD
                 post_date = datetime.strptime(p_date_str, "%Y-%m-%d")
        except:
             print(f"    [Date Parse Error] {p_date_str}")

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

def main():
    print("Waiting for DB to be ready...", flush=True)
    time.sleep(10) # Simple wait for DB
    
    while True:
        try:
            asyncio.run(run_task())
        except Exception as e:
            print(f"[!] Error in main loop: {e}")
        
        print("\n[-] Task finished. Waiting for next schedule (60 sec)...")
        time.sleep(60)


if __name__ == "__main__":
    main()
