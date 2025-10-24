"""
Export collected articles for sentiment analysis
Usage: python export_for_sentiment.py TICKER [days_back]
"""
import sys
import os
from utils.article_retriever import ArticleRetriever


def main():
    if len(sys.argv) < 2:
        print("Usage: python export_for_sentiment.py TICKER [days_back]")
        print("Example: python export_for_sentiment.py AMZN 30")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    days_back = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    retriever = ArticleRetriever()
    
    # Export to data directory
    output_dir = os.path.join(
        os.path.dirname(__file__), 
        "data", 
        "sentiment_ready"
    )
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"{ticker}_articles.json")
    
    count = retriever.export_for_sentiment_analysis(
        ticker=ticker,
        output_file=output_file,
        days_back=days_back
    )
    
    print(f"\n✅ Ready for sentiment analysis: {output_file}")
    print(f"📊 Total articles: {count}")


if __name__ == "__main__":
    main()