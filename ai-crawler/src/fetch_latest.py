import asyncio
from crawler import NaverCafeCrawler
import json

async def main():
    # URL and Keyword
    cafe_url = "https://cafe.naver.com/m2school"
    keyword = "윌비스"
    
    # Initialize Crawler (No login credentials provided by default)
    # If you have login info, pass nid='id', npw='password'
    crawler = NaverCafeCrawler(cafe_url, keyword)
    
    # Crawl only the latest 1 post
    print(f"[*] Searching for '{keyword}' in {cafe_url}...")
    results = await crawler.crawl(limit=1, headless=False) # headless=False to see the browser
    
    if results:
        latest_post = results[0]
        print("\n" + "="*50)
        print(f" 제목: {latest_post.get('title')}")
        print(f" 날짜: {latest_post.get('post_date_str')}")
        print(f" 링크: {latest_post.get('link')}")
        print("-" * 50)
        print(" [내용 요약]")
        print(latest_post.get('content', '내용 없음 (접근 권한 필요 가능성)'))
        print("="*50 + "\n")
    else:
        print("[!] 게시글을 찾을 수 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
