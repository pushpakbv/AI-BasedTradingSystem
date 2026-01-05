import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import json
import numpy as np



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
        """Process company with detailed logging"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 PROCESSING: {ticker}")
        logger.info(f"{'='*70}")
        
        try:
            # Step 1: Read articles
            logger.info(f"[1/5] Reading articles...")
            articles = self.read_articles_for_company(ticker)
            
            if not articles:
                logger.warning(f"⚠️ No articles found")
                return
            
            logger.info(f"✅ Found {len(articles)} articles")
            
            # Step 2: Classify
            logger.info(f"[2/5] Classifying articles...")
            general_articles = []
            financial_articles = []
            
            for article in articles:
                try:
                    result = self.classifier.classify_article(article)
                    category = result if isinstance(result, str) else result.get('category', 'general')
                    
                    if category == 'financial':
                        financial_articles.append(article)
                    else:
                        general_articles.append(article)
                except Exception as e:
                    logger.debug(f"Classification error: {e}")
                    general_articles.append(article)
            
            logger.info(f"✅ Classified: {len(general_articles)} general, {len(financial_articles)} financial")
            
            # Step 3: Sentiment Analysis - THIS IS CRITICAL
            logger.info(f"[3/5] Analyzing sentiment for {len(articles)} articles...")
            sentiment_scores = []
            
            for i, article in enumerate(articles):
                content = article.get('content', '') or article.get('summary', '')
                
                if not content:
                    logger.debug(f"  {i+1}/{len(articles)}: No content")
                    sentiment_scores.append(0.0)
                    continue
                
                try:
                    result = self.sentiment_analyzer.analyze(content)
                    score = result.get('score', 0.0)
                    sentiment_scores.append(float(score))
                    logger.debug(f"  {i+1}/{len(articles)}: {article.get('title', 'N/A')[:50]}... → {score:.3f}")
                    
                except Exception as e:
                    logger.warning(f"  {i+1}/{len(articles)}: Error - {e}")
                    sentiment_scores.append(0.0)
            
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            logger.info(f"✅ Sentiment: avg={avg_sentiment:.3f}, min={min(sentiment_scores) if sentiment_scores else 0:.3f}, max={max(sentiment_scores) if sentiment_scores else 0:.3f}")
            
            # Step 4: Financial events
            logger.info(f"[4/5] Analyzing financial events...")
            financial_events = []
            
            for article in financial_articles[:5]:  # Limit to first 5
                try:
                    if hasattr(self.financial_classifier, 'classify'):
                        events = self.financial_classifier.classify(article.get('content', ''))
                        if events:
                            financial_events.extend(events)
                except:
                    pass
            
            logger.info(f"✅ Financial events: {len(financial_events)}")
            
            # Step 5: Generate prediction
            logger.info(f"[5/5] Generating prediction...")
            prediction = self._generate_prediction(
                ticker, 
                len(articles), 
                avg_sentiment, 
                len(financial_events), 
                financial_events
            )
            
            # Save
            output_file = OUTPUT_DIR / f"{ticker}_prediction.json"
            with open(output_file, 'w') as f:
                json.dump(prediction, f, indent=2, default=str)
            
            logger.info(f"✅ Saved to {output_file}")
            logger.info(f"{'='*70}\n")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)

    def _generate_prediction(self, ticker, total_articles, avg_sentiment, financial_event_count, financial_data):
        """Generate final prediction from analysis results"""
        try:
            logger.info(f"📊 {ticker}: Avg sentiment = {avg_sentiment:.3f}, Financial events = {financial_event_count}")
            
            # Determine signal with LOWER thresholds for more diverse signals
            if financial_event_count > 0:
                # Financial events detected - weight them heavily
                financial_strength = min(financial_event_count / max(total_articles, 1), 1.0)
                combined_score = avg_sentiment * 0.5 + (financial_strength * 0.5)
                
                if combined_score > 0.5:
                    final_signal = 'STRONG_BUY'
                    direction = 'BULLISH'
                elif combined_score > 0.15:
                    final_signal = 'BUY'
                    direction = 'BULLISH'
                elif combined_score < -0.5:
                    final_signal = 'STRONG_SELL'
                    direction = 'BEARISH'
                elif combined_score < -0.15:
                    final_signal = 'SELL'
                    direction = 'BEARISH'
                else:
                    final_signal = 'HOLD'
                    direction = 'NEUTRAL'
            else:
                # No financial events - use sentiment only with LOWER thresholds
                combined_score = avg_sentiment
                
                # ✅ FIXED: Lower thresholds for more diverse signals
                if avg_sentiment > 0.3:  # Was 0.4, now 0.3
                    final_signal = 'STRONG_BUY' if avg_sentiment > 0.6 else 'BUY'
                    direction = 'BULLISH'
                elif avg_sentiment > 0.1:  # NEW: Range for weak BUY
                    final_signal = 'BUY'
                    direction = 'BULLISH'
                elif avg_sentiment < -0.3:  # Was -0.4, now -0.3
                    final_signal = 'STRONG_SELL' if avg_sentiment < -0.6 else 'SELL'
                    direction = 'BEARISH'
                elif avg_sentiment < -0.1:  # NEW: Range for weak SELL
                    final_signal = 'SELL'
                    direction = 'BEARISH'
                else:
                    final_signal = 'HOLD'
                    direction = 'NEUTRAL'
            
            # Clamp combined score
            combined_score = max(-1, min(1, combined_score))
            
            # Confidence: Based on article count + sentiment magnitude
            confidence = min(
                0.95, 
                (abs(avg_sentiment) * 0.6) +  # Sentiment strength
                (min(total_articles / 20, 1.0) * 0.4)  # Article volume
            )
            
            confidence_level = 'HIGH' if confidence > 0.7 else 'MEDIUM' if confidence > 0.4 else 'LOW'
            
            logger.info(f"  ✅ {final_signal} ({direction}) - Score: {combined_score:.3f}, Confidence: {confidence_level}")
            
            return {
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'total_articles': total_articles,
                'average_sentiment': round(float(avg_sentiment), 3),
                'financial_events': financial_event_count,
                'confidence': round(float(confidence), 3),
                'prediction': {
                    'final_signal': final_signal,
                    'direction': direction,
                    'combined_score': round(float(combined_score), 3),
                    'confidence_level': confidence_level,
                    'reasoning': self._generate_reasoning(final_signal, avg_sentiment, financial_event_count, total_articles)
                },
                'components': {
                    'general_sentiment': {
                        'score': round(avg_sentiment, 3),
                        'contribution': round(avg_sentiment * 0.6, 3),
                        'weight': 0.6
                    },
                    'financial_signal': {
                        'score': round((financial_event_count / max(total_articles, 1)), 3),
                        'contribution': round((financial_event_count / max(total_articles, 1)) * 0.4, 3),
                        'weight': 0.4
                    }
                },
                'data_sources': {
                    'general_articles': total_articles - financial_event_count,
                    'financial_articles': financial_event_count,
                    'total_articles': total_articles
                }
            }
        except Exception as e:
            logger.error(f"❌ Error generating prediction: {e}", exc_info=True)
            return {
                'ticker': ticker,
                'timestamp': datetime.now().isoformat(),
                'total_articles': 0,
                'average_sentiment': 0,
                'financial_events': 0,
                'confidence': 0,
                'prediction': {
                    'final_signal': 'HOLD',
                    'direction': 'NEUTRAL',
                    'combined_score': 0,
                    'confidence_level': 'LOW',
                    'reasoning': 'Error generating prediction'
                }
            }
    
    def _generate_reasoning(self, signal, sentiment, event_count, total_articles):
        """Generate human-readable reasoning"""
        reasons = []
        
        # Sentiment reasoning
        if sentiment > 0.5:
            reasons.append("Very strong positive sentiment")
        elif sentiment > 0.3:
            reasons.append("Strong positive sentiment")
        elif sentiment > 0.1:
            reasons.append("Positive sentiment")
        elif sentiment < -0.5:
            reasons.append("Very strong negative sentiment")
        elif sentiment < -0.3:
            reasons.append("Strong negative sentiment")
        elif sentiment < -0.1:
            reasons.append("Negative sentiment")
        else:
            reasons.append("Neutral sentiment")
        
        # Financial events
        if event_count > 3:
            reasons.append(f"Multiple ({event_count}) financial events")
        elif event_count > 0:
            reasons.append(f"{event_count} financial event(s)")
        
        # Volume
        if total_articles > 30:
            reasons.append(f"Based on {total_articles} articles")
        elif total_articles > 15:
            reasons.append(f"Based on {total_articles} articles")
        elif total_articles > 5:
            reasons.append(f"Based on {total_articles} article(s)")
        elif total_articles > 0:
            reasons.append(f"Limited data ({total_articles} article)")
        
        return " | ".join(reasons) if reasons else "Insufficient data"    
    


    
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