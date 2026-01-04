"""
Article Classifier: Separates general company news from financial news
Uses keyword matching and NLP to determine article type
"""
import os
import json
import logging
from typing import Dict, List, Tuple
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleClassifier:
    """Classifies articles as 'general' or 'financial' based on content"""
    
    def __init__(self):
        # Financial keywords - strong indicators
        self.financial_keywords = {
            'earnings', 'revenue', 'profit', 'loss', 'quarterly', 'q1', 'q2', 'q3', 'q4',
            'fiscal', 'eps', 'ebitda', 'dividend', 'shares', 'stock price', 'market cap',
            'valuation', 'guidance', 'forecast', 'outlook', 'analyst', 'rating',
            'upgrade', 'downgrade', 'buy', 'sell', 'hold', 'price target',
            'ipo', 'merger', 'acquisition', 'deal', 'investment', 'investor',
            'sec filing', '10-k', '10-q', '8-k', 'balance sheet', 'cash flow',
            'debt', 'credit', 'bond', 'yield', 'return', 'margin', 'growth rate',
            'sales figures', 'financial results', 'financial performance',
            'beat estimates', 'miss estimates', 'wall street', 'trading',
            'quarterly report', 'annual report', 'financial statement'
        }
        
        # General news keywords
        self.general_keywords = {
            'launches', 'announces', 'unveils', 'introduces', 'releases',
            'partnership', 'collaboration', 'agreement', 'contract', 'deal',
            'expansion', 'opening', 'facility', 'factory', 'warehouse',
            'hiring', 'layoff', 'workforce', 'employee', 'ceo', 'executive',
            'product', 'service', 'feature', 'technology', 'innovation',
            'customer', 'user', 'client', 'market share', 'competition',
            'regulation', 'lawsuit', 'legal', 'settlement', 'investigation',
            'sustainability', 'environment', 'carbon', 'renewable',
            'award', 'recognition', 'milestone', 'achievement',
            'event', 'conference', 'summit', 'expo'
        }
    
    def classify_article(self, article: Dict) -> str:
        """
        Classify article as 'financial' or 'general'
        
        Args:
            article: Article dictionary with 'title' and 'content'
            
        Returns:
            'financial' or 'general'
        """
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        
        # Combine title and content, but weight title more heavily
        full_text = f"{title} {title} {content}"
        
        # Count keyword matches
        financial_score = sum(1 for keyword in self.financial_keywords if keyword in full_text)
        general_score = sum(1 for keyword in self.general_keywords if keyword in full_text)
        
        # Check for financial patterns (numbers with $ or %)
        financial_patterns = [
            r'\$\d+\.?\d*\s*(billion|million|trillion)',  # $5 billion
            r'\d+\.?\d*%',  # 5.3%
            r'q[1-4]\s+\d{4}',  # Q3 2025
            r'fiscal\s+year',
            r'earnings?\s+per\s+share',
            r'price\s+target',
        ]
        
        for pattern in financial_patterns:
            if re.search(pattern, full_text):
                financial_score += 2  # Strong indicator
        
        # Check title specifically for financial indicators
        if any(keyword in title for keyword in ['earnings', 'revenue', 'profit', 'stock', 'q1', 'q2', 'q3', 'q4']):
            financial_score += 3
        
        # Decision logic
        if financial_score > general_score * 1.5:  # Financial must be significantly higher
            return 'financial'
        else:
            return 'general'
    
    def classify_and_split(
        self, 
        input_dir: str,
        output_dir: str
    ) -> Tuple[int, int]:
        """
        Read articles from crawler output and split into general/financial
        
        Args:
            input_dir: Path to crawler_service/data/by_company
            output_dir: Path to data_processor_service/classified_articles
            
        Returns:
            Tuple of (general_count, financial_count)
        """
        general_count = 0
        financial_count = 0
        
        # Create output directories
        general_dir = os.path.join(output_dir, "general")
        financial_dir = os.path.join(output_dir, "financial")
        os.makedirs(general_dir, exist_ok=True)
        os.makedirs(financial_dir, exist_ok=True)
        
        logger.info("=" * 70)
        logger.info("ARTICLE CLASSIFICATION STARTING")
        logger.info("=" * 70)
        
        # Process each company folder
        for ticker in os.listdir(input_dir):
            ticker_path = os.path.join(input_dir, ticker)
            
            if not os.path.isdir(ticker_path):
                continue
            
            company_general = []
            company_financial = []
            
            # Process each date folder
            for date_folder in os.listdir(ticker_path):
                date_path = os.path.join(ticker_path, date_folder)
                
                if not os.path.isdir(date_path):
                    continue
                
                # Process each article
                for filename in os.listdir(date_path):
                    if not filename.endswith('.json'):
                        continue
                    
                    filepath = os.path.join(date_path, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            article = json.load(f)
                        
                        # Classify article
                        article_type = self.classify_article(article)
                        
                        # Add classification metadata
                        article['classification'] = article_type
                        article['classified_at'] = datetime.utcnow().isoformat() + 'Z'
                        
                        if article_type == 'financial':
                            company_financial.append(article)
                            financial_count += 1
                        else:
                            company_general.append(article)
                            general_count += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing {filepath}: {e}")
            
            # Save classified articles by company
            if company_general:
                output_file = os.path.join(general_dir, f"{ticker}_general.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(company_general, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ {ticker}: {len(company_general)} general articles")
            
            if company_financial:
                output_file = os.path.join(financial_dir, f"{ticker}_financial.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(company_financial, f, indent=2, ensure_ascii=False)
                logger.info(f"💰 {ticker}: {len(company_financial)} financial articles")
        
        

        logger.info("=" * 70)
        logger.info(f"CLASSIFICATION COMPLETE")
        logger.info(f"General articles: {general_count}")
        logger.info(f"Financial articles: {financial_count}")
        logger.info(f"Total: {general_count + financial_count}")
        logger.info("=" * 70)
        
        return general_count, financial_count


def main():
    """Run article classification"""
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, "crawler_service", "data", "by_company")
    output_dir = os.path.join(base_dir, "data_processor_service", "classified_articles")
    
    # Classify articles
    classifier = ArticleClassifier()
    general_count, financial_count = classifier.classify_and_split(input_dir, output_dir)
    
    print(f"\n✅ Classification complete!")
    print(f"📰 General news: {general_count} articles")
    print(f"💰 Financial news: {financial_count} articles")
    print(f"\nOutput location: {output_dir}")


if __name__ == "__main__":
    main()