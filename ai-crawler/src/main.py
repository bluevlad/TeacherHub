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
                INSERT INTO reputation_data (keyword, site_name, title, url, sentiment, score)
                VALUES (:keyword, :site_name, :title, :url, :sentiment, :score)
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
    for post in posts:
        full_text = f"{post['title']} {post['content']} {' '.join(post['comments'])}"
        result = analyzer.analyze(full_text)
        
        db_data = {
            "keyword": KEYWORD,
            "site_name": SITE_NAME,
            "title": post['title'],
            "url": post['url'],
            "sentiment": result['label'],
            "score": result['score']
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
