import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
CUR_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = CUR_DIR.parent
if str(CUR_DIR) not in sys.path:
    sys.path.insert(0, str(CUR_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import modules
from article_classifier import ArticleClassifier
from sentiment_analysis import SentimentAnalyzer
from financial_analyzer.financial_event_classifier import FinancialEventClassifier
from financial_analyzer.earnings_parser import EarningsParser
from financial_analyzer.market_predictor import MarketImpactPredictor
from financial_analyzer.signal_combiner import SignalCombiner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths - USE ENVIRONMENT VARIABLE FIRST
crawler_data_env = os.getenv('CRAWLER_DATA_DIR')
if crawler_data_env and os.path.exists(crawler_data_env):
    CRAWLER_DIR = Path(crawler_data_env)
else:
    # In Docker, use /app path; locally use relative path
    if os.path.exists('/app/crawler_service'):
        CRAWLER_DIR = Path('/app/crawler_service/data/by_company')
    else:
        CRAWLER_DIR = CUR_DIR.parent / "crawler_service" / "data" / "by_company"

OUTPUT_DIR = CUR_DIR / "final_predictions"
CLASSIFIED_DIR = CUR_DIR / "classified_articles"
SENTIMENT_DIR = CUR_DIR / "sentiment_results"
FINANCIAL_DIR = CUR_DIR / "financial_analysis_results"


class ProcessingPipeline:
    """Orchestrates the complete data processing pipeline"""
    
    def __init__(self):
        logger.info("🚀 Initializing Processing Pipeline...")
        logger.info(f"Crawler directory: {CRAWLER_DIR}")
        
        # Create output directories
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        CLASSIFIED_DIR.mkdir(parents=True, exist_ok=True)
        SENTIMENT_DIR.mkdir(parents=True, exist_ok=True)
        FINANCIAL_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize modules
        self.classifier = ArticleClassifier()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.financial_classifier = FinancialEventClassifier()
        self.earnings_parser = EarningsParser()
        self.market_predictor = MarketImpactPredictor()
        self.signal_combiner = SignalCombiner()
        
        logger.info("✅ Pipeline initialized successfully")
    
    def get_companies_from_crawler(self):
        """Get list of companies that have crawled data"""
        if not CRAWLER_DIR.exists():
            logger.warning(f"⚠️ Crawler directory not found: {CRAWLER_DIR}")
            return []
        
        companies = [d for d in os.listdir(CRAWLER_DIR) 
                    if os.path.isdir(CRAWLER_DIR / d)]
        logger.info(f"📂 Found {len(companies)} companies with crawled data: {companies}")
        return sorted(companies)
    
    def read_articles_for_company(self, ticker):
        """Read all articles for a company from crawler output"""
        ticker_dir = CRAWLER_DIR / ticker
        articles = []
        
        if not ticker_dir.exists():
            logger.warning(f"⚠️ No directory found for {ticker} at {ticker_dir}")
            return articles
        
        # Recursively find all JSON files
        for json_file in ticker_dir.rglob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    article = json.load(f)
                    articles.append(article)
            except Exception as e:
                logger.warning(f"⚠️ Failed to read {json_file}: {e}")
        
        logger.info(f"📖 Loaded {len(articles)} articles for {ticker}")
        return articles
    
    def process_company(self, ticker):
        """Process all data for a single company"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 PROCESSING: {ticker}")
        logger.info(f"{'='*70}")
        
        try:
            # Step 1: Read articles
            logger.info(f"[1/5] Reading articles for {ticker}...")
            articles = self.read_articles_for_company(ticker)
            
            if not articles:
                logger.warning(f"⚠️ No articles found for {ticker}")
                return
            
            logger.info(f"✅ Found {len(articles)} articles")
            
            # Step 2: Classify articles
            logger.info(f"[2/5] Classifying articles...")
            general_articles = []
            financial_articles = []
            
            for article in articles:
                try:
                    # Pass the FULL article dict, not just content
                    result = self.classifier.classify_article(article)
                    
                    # Normalize result to always be a dict
                    if isinstance(result, str):
                        # Result is just a category string
                        category = result
                        result_dict = {'category': category}
                    elif isinstance(result, dict):
                        # Result is already a dict
                        category = result.get('category', 'general')
                        result_dict = result
                    else:
                        # Unknown result type, default to general
                        category = 'general'
                        result_dict = {'category': 'general'}
                    
                    if category == 'financial':
                        financial_articles.append({**article, 'classification': result_dict})
                    else:
                        general_articles.append({**article, 'classification': result_dict})
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to classify '{article.get('title', 'unknown')}': {type(e).__name__}: {str(e)}")
                    general_articles.append(article)
                    
                                
            logger.info(f"✅ Classified: {len(general_articles)} general, {len(financial_articles)} financial")
            
            # Step 3: Sentiment Analysis
            logger.info(f"[3/5] Analyzing sentiment...")
            sentiment_data = {}
            
            for article in articles:
                try:
                    content = article.get('content', '')
                    title = article.get('title', 'unknown')
                    
                    # Try different method names
                    if hasattr(self.sentiment_analyzer, 'analyze'):
                        sentiment = self.sentiment_analyzer.analyze(content)
                    elif hasattr(self.sentiment_analyzer, 'get_sentiment'):
                        sentiment = self.sentiment_analyzer.get_sentiment(content)
                    elif hasattr(self.sentiment_analyzer, 'predict'):
                        sentiment = self.sentiment_analyzer.predict(content)
                    else:
                        sentiment = {'score': 0, 'label': 'neutral'}
                    
                    # Normalize sentiment to dict if it's a string
                    if isinstance(sentiment, str):
                        sentiment = {'label': sentiment, 'score': 0}
                    elif not isinstance(sentiment, dict):
                        sentiment = {'score': 0, 'label': 'neutral'}
                    
                    sentiment_data[title] = sentiment
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to analyze sentiment for '{title}': {type(e).__name__}")
                    sentiment_data[title] = {'score': 0, 'label': 'neutral'}
            
            logger.info(f"✅ Sentiment analysis complete")
            
            # Step 4: Financial Event Classification
            logger.info(f"[4/5] Financial event analysis...")
            financial_events = []
            
            for article in financial_articles:
                try:
                    content = article.get('content', '')
                    
                    if hasattr(self.financial_classifier, 'classify'):
                        events = self.financial_classifier.classify(content)
                    else:
                        events = []
                    
                    if events and isinstance(events, list):
                        financial_events.extend(events)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed financial analysis: {type(e).__name__}")
            
            logger.info(f"✅ Found {len(financial_events)} financial events")
            
            # Step 5: Market Prediction
            logger.info(f"[5/5] Generating market prediction...")
            prediction = self._generate_prediction(ticker, len(articles), sentiment_data, financial_events)
            
            # Save prediction
            output_file = OUTPUT_DIR / f"{ticker}_prediction.json"
            with open(output_file, 'w') as f:
                json.dump(prediction, f, indent=2, default=str)
            
            logger.info(f"✅ Prediction saved to {output_file}")
            logger.info(f"{'='*70}")
            
        except Exception as e:
            logger.error(f"❌ Error processing {ticker}: {e}", exc_info=True)

    def _generate_prediction(self, ticker, total_articles, sentiment_data, financial_data):
        """Generate final prediction from analysis results"""
        try:
            avg_sentiment = sum(s.get('score', 0) for s in sentiment_data.values()) / len(sentiment_data) if sentiment_data else 0
            
            return {
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'total_articles': total_articles,
                'average_sentiment': avg_sentiment,
                'financial_events': len(financial_data),
                'confidence': min(0.95, len(financial_data) * 0.1 + abs(avg_sentiment) * 0.5)
            }
        except Exception as e:
            logger.error(f"❌ Error generating prediction: {e}", exc_info=True)
            return {}
    
    def run(self):
        """Run the complete pipeline"""
        logger.info("\n" + "="*70)
        logger.info("🚀 STARTING COMPLETE PROCESSING PIPELINE")
        logger.info("="*70)
        
        companies = self.get_companies_from_crawler()
        
        if not companies:
            logger.warning("⚠️ No companies found in crawler directory")
            return
        
        successful = 0
        failed = 0
        
        for ticker in companies:
            try:
                self.process_company(ticker)
                successful += 1
            except Exception as e:
                logger.error(f"❌ Failed to process {ticker}: {e}", exc_info=True)
                failed += 1
        
        logger.info("\n" + "="*70)
        logger.info("✅ PIPELINE COMPLETE")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total: {successful + failed}")
        logger.info(f"Output: {OUTPUT_DIR}")
        logger.info("="*70 + "\n")


def main():
    """Main entry point"""
    pipeline = ProcessingPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()