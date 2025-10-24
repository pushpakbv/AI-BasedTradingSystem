"""
CLI tool to retrieve articles for a company on a specific date.
Usage: python crawler_service/get_daily_articles.py FDX 2025-01-16
"""
import sys
import os
import json
from datetime import datetime, timedelta

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler_service.utils.article_retriever import ArticleRetriever


def main():
    if len(sys.argv) < 2:
        print("Usage: python get_daily_articles.py <TICKER> [DATE]")
        print("Example: python get_daily_articles.py FDX 2025-01-16")
        print("\nAvailable companies:")
        retriever = ArticleRetriever()
        companies = retriever.get_all_tracked_companies()
        for company in companies:
            print(f"  - {company}")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    
    # Default to today if no date provided
    if len(sys.argv) >= 3:
        date = sys.argv[2]
    else:
        date = datetime.utcnow().strftime("%Y-%m-%d")
    
    retriever = ArticleRetriever()
    
    # Get articles
    articles = retriever.get_articles_for_company_date(ticker, date)
    
    if not articles:
        print(f"\nNo articles found for {ticker} on {date}")
        
        # Show available dates
        available = retriever.get_available_dates_for_company(ticker)
        if available:
            print(f"\nAvailable dates for {ticker}:")
            for d in available[-10:]:  # Show last 10 dates
                print(f"  - {d}")
        else:
            print(f"\nNo data found for {ticker}")
        
        sys.exit(0)
    
    print(f"\n{'='*80}")
    print(f"Articles for {ticker} on {date}")
    print(f"{'='*80}")
    print(f"Total articles: {len(articles)}\n")
    
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   Source: {article['source_domain']}")
        print(f"   Mentions: {article.get('primary_company', {}).get('mentions', 0)}")
        print(f"   Word Count: {article['word_count']}")
        print(f"   Relevance: {article['relevance_score']:.2f}")
        print()
    
    # Option to export combined text
    print("\nOptions:")
    print("  1. Show full text")
    print("  2. Export to JSON")
    print("  3. Export combined text for ML")
    
    choice = input("\nSelect option (or press Enter to skip): ").strip()
    
    if choice == "1":
        combined = retriever.get_combined_text_for_date(ticker, date)
        print(f"\n{'='*80}")
        print("COMBINED TEXT")
        print(f"{'='*80}\n")
        print(combined)
    
    elif choice == "2":
        output_file = f"{ticker}_{date}_articles.json"
        with open(output_file, "w", encoding="utf-8") as fh:
            json.dump(articles, fh, ensure_ascii=False, indent=2)
        print(f"\nExported to: {output_file}")
    
    elif choice == "3":
        combined = retriever.get_combined_text_for_date(ticker, date)
        output_file = f"{ticker}_{date}_combined.txt"
        with open(output_file, "w", encoding="utf-8") as fh:
            fh.write(combined)
        print(f"\nExported combined text to: {output_file}")
        print(f"Character count: {len(combined)}")
        print(f"Word count: {len(combined.split())}")


if __name__ == "__main__":
    main()