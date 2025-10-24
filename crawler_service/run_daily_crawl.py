"""
Daily Crawler Runner
Runs the crawler for today's articles only and generates a summary.
Usage: python crawler_service/run_daily_crawl.py
"""
import os
import sys
import datetime
import logging

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler_service.main import main as run_crawler
from crawler_service.utils.article_retriever import ArticleRetriever

def generate_daily_summary():
    """Generate summary of today's crawl results"""
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    retriever = ArticleRetriever()
    
    print("\n" + "=" * 80)
    print(f"📊 DAILY CRAWL SUMMARY - {today}")
    print("=" * 80)
    
    companies = retriever.get_all_tracked_companies()
    total_articles = 0
    
    for ticker in companies:
        articles = retriever.get_articles_for_company_date(ticker, today)
        if articles:
            total_articles += len(articles)
            print(f"\n✅ {ticker}: {len(articles)} articles")
            for i, article in enumerate(articles[:5], 1):  # Show top 5
                print(f"   {i}. {article['title'][:70]}")
                print(f"      Mentions: {article.get('primary_company', {}).get('mentions', 0)} | "
                      f"Words: {article['word_count']} | "
                      f"Source: {article['source_domain']}")
    
    print("\n" + "=" * 80)
    print(f"📈 TOTAL: {total_articles} articles across {len(companies)} companies")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n🚀 Starting daily crawl...")
    print(f"📅 Target date: {datetime.datetime.utcnow().strftime('%Y-%m-%d')}")
    print("🎯 Mode: Company-specific articles only")
    print("🆓 Sources: Free news sites only\n")
    
    # Run the crawler
    try:
        run_crawler()
    except Exception as e:
        print(f"\n❌ Crawler error: {e}")
        sys.exit(1)
    
    # Generate summary
    print("\n✅ Crawl completed! Generating summary...\n")
    generate_daily_summary()