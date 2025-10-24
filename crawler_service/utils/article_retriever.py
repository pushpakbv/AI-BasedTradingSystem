"""
Article Retrieval Utility
Easy access to collected company-specific articles for sentiment analysis
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import glob


class ArticleRetriever:
    """Retrieve and filter collected articles for sentiment analysis"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data", "by_company")
        
        self.data_dir = data_dir
    
    def get_all_tracked_companies(self) -> List[str]:
        """Get list of all company tickers with collected data"""
        if not os.path.exists(self.data_dir):
            return []
        
        return [d for d in os.listdir(self.data_dir) 
                if os.path.isdir(os.path.join(self.data_dir, d))]
    
    def get_articles_for_company(
        self, 
        ticker: str, 
        days_back: int = 30,
        min_word_count: int = 0
    ) -> List[Dict]:
        """
        Get all articles for a specific company
        
        Args:
            ticker: Company ticker symbol
            days_back: Number of days to look back (0 = all time)
            min_word_count: Minimum article word count
            
        Returns:
            List of article dictionaries
        """
        company_dir = os.path.join(self.data_dir, ticker)
        if not os.path.exists(company_dir):
            return []
        
        articles = []
        cutoff_date = None
        
        if days_back > 0:
            cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Search all date subdirectories
        for date_dir in os.listdir(company_dir):
            date_path = os.path.join(company_dir, date_dir)
            if not os.path.isdir(date_path):
                continue
            
            # Check date filter
            if cutoff_date:
                try:
                    dir_date = datetime.strptime(date_dir, "%Y-%m-%d")
                    if dir_date < cutoff_date:
                        continue
                except:
                    pass
            
            # Load all articles from this date
            for article_file in glob.glob(os.path.join(date_path, "*.json")):
                try:
                    with open(article_file, 'r', encoding='utf-8') as f:
                        article = json.load(f)
                    
                    # Apply word count filter
                    if article.get('word_count', 0) >= min_word_count:
                        articles.append(article)
                        
                except Exception as e:
                    print(f"Error loading {article_file}: {e}")
        
        # Sort by date (newest first)
        articles.sort(
            key=lambda x: x.get('published_datetime', x.get('fetched_at', '')), 
            reverse=True
        )
        
        return articles
    
    def get_articles_for_company_date(
        self, 
        ticker: str, 
        date: str
    ) -> List[Dict]:
        """
        Get articles for a specific company on a specific date
        
        Args:
            ticker: Company ticker symbol
            date: Date string in YYYY-MM-DD format
            
        Returns:
            List of article dictionaries
        """
        date_path = os.path.join(self.data_dir, ticker, date)
        if not os.path.exists(date_path):
            return []
        
        articles = []
        for article_file in glob.glob(os.path.join(date_path, "*.json")):
            try:
                with open(article_file, 'r', encoding='utf-8') as f:
                    articles.append(json.load(f))
            except Exception as e:
                print(f"Error loading {article_file}: {e}")
        
        return articles
    
    def get_article_count_by_company(self, days_back: int = 30) -> Dict[str, int]:
        """Get article counts for all companies"""
        counts = {}
        
        for ticker in self.get_all_tracked_companies():
            articles = self.get_articles_for_company(ticker, days_back=days_back)
            counts[ticker] = len(articles)
        
        return counts
    
    def export_for_sentiment_analysis(
        self, 
        ticker: str, 
        output_file: str,
        days_back: int = 30
    ):
        """
        Export articles in format ready for sentiment analysis
        
        Args:
            ticker: Company ticker
            output_file: Output JSON file path
            days_back: Days to include
        """
        articles = self.get_articles_for_company(ticker, days_back=days_back)
        
        # Extract only fields needed for sentiment analysis
        sentiment_data = []
        for article in articles:
            sentiment_data.append({
                'id': article.get('url', ''),
                'date': article.get('published_date', ''),
                'datetime': article.get('published_datetime', ''),
                'title': article.get('title', ''),
                'content': article.get('content', ''),
                'source': article.get('source_domain', ''),
                'company_ticker': ticker,
                'company_name': article.get('primary_company', {}).get('name', ''),
                'mentions': article.get('primary_company', {}).get('mentions', 0),
                'word_count': article.get('word_count', 0),
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sentiment_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(sentiment_data)} articles for {ticker} to {output_file}")
        return len(sentiment_data)


if __name__ == "__main__":
    # Example usage
    retriever = ArticleRetriever()
    
    print("=" * 60)
    print("COLLECTED ARTICLES SUMMARY")
    print("=" * 60)
    
    counts = retriever.get_article_count_by_company(days_back=30)
    total = sum(counts.values())
    
    for ticker, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{ticker:10s}: {count:4d} articles")
    
    print("=" * 60)
    print(f"TOTAL: {total} articles across {len(counts)} companies")
    print("=" * 60)