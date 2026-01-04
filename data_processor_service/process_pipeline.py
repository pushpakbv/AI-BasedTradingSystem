"""
Complete Processing Pipeline
Processes existing articles through the entire analysis pipeline
"""
import os
import sys
import json
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

# Paths
CRAWLER_DIR = CUR_DIR.parent / "crawler_service" / "data" / "by_company"
OUTPUT_DIR = CUR_DIR / "final_predictions"
CLASSIFIED_DIR = CUR_DIR / "classified_articles"
SENTIMENT_DIR = CUR_DIR / "sentiment_results"
FINANCIAL_DIR = CUR_DIR / "financial_analysis_results"


class ProcessingPipeline:
    """Orchestrates the complete data processing pipeline"""
    
    def __init__(self):
        logger.info("🚀 Initializing Processing Pipeline...")
        
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
        logger.info(f"📂 Found {len(companies)} companies with crawled data")
        return sorted(companies)
    
    def read_articles_for_company(self, ticker):
        """Read all articles for a company from crawler output"""
        ticker_dir = CRAWLER_DIR / ticker
        articles = []
        
        if not ticker_dir.exists():
            logger.warning(f"⚠️ No data found for {ticker}")
            return articles
        
        # Recursively find all JSON files
        for json_file in ticker_dir.rglob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    article = json.load(f)
                    articles.append(article)
            except Exception as e:
                logger.error(f"❌ Failed to read {json_file}: {e}")
        
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
                return False
            
            logger.info(f"✅ Found {len(articles)} articles")
            
            # Step 2: Classify articles
            logger.info(f"[2/5] Classifying articles...")
            general_articles = []
            financial_articles = []
            
            for article in articles:
                try:
                    classification = self.classifier.classify_article(article)
                    article['classification'] = classification
                    article['classified_at'] = datetime.utcnow().isoformat() + 'Z'
                    
                    if classification == 'financial':
                        financial_articles.append(article)
                    else:
                        general_articles.append(article)
                except Exception as e:
                    logger.error(f"❌ Classification failed: {e}")
            
            logger.info(f"✅ Classified: {len(general_articles)} general, {len(financial_articles)} financial")
            
            # Step 3: Sentiment analysis
            logger.info(f"[3/5] Analyzing sentiment...")
            sentiment_results = {
                'ticker': ticker,
                'general_sentiment': [],
                'financial_sentiment': [],
                'analyzed_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            for article in general_articles:
                try:
                    text = article.get('content', '') or article.get('summary', '')
                    if not text:
                        continue
                    
                    result = self.sentiment_analyzer.analyze_text(text)
                    sentiment_results['general_sentiment'].append({
                        'title': article.get('title', ''),
                        'sentiment': result.get('label', 'neutral'),
                        'score': result.get('score', 0)
                    })
                except Exception as e:
                    logger.error(f"❌ Sentiment analysis failed: {e}")
            
            for article in financial_articles:
                try:
                    text = article.get('content', '') or article.get('summary', '')
                    if not text:
                        continue
                    
                    result = self.sentiment_analyzer.analyze_text(text)
                    sentiment_results['financial_sentiment'].append({
                        'title': article.get('title', ''),
                        'sentiment': result.get('label', 'neutral'),
                        'score': result.get('score', 0)
                    })
                except Exception as e:
                    logger.error(f"❌ Sentiment analysis failed: {e}")
            
            logger.info(f"✅ Sentiment analysis complete")
            
            # Save sentiment results
            sentiment_file = SENTIMENT_DIR / f"{ticker}_sentiment.json"
            with open(sentiment_file, 'w') as f:
                json.dump(sentiment_results, f, indent=2)
            
            # Step 4: Financial event classification
            logger.info(f"[4/5] Classifying financial events...")
            financial_events = {
                'ticker': ticker,
                'events': [],
                'analyzed_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            for article in financial_articles:
                try:
                    text = article.get('content', '') or article.get('summary', '')
                    if not text:
                        continue
                    
                    # ✅ Use analyze_financial_article method
                    try:
                        result = self.financial_classifier.analyze_financial_article(text)
                        
                        # Handle different return types
                        if result:
                            # If result is a string, try to parse it as JSON
                            if isinstance(result, str):
                                try:
                                    result = json.loads(result)
                                except:
                                    # If not JSON, skip this result
                                    logger.debug(f"⚠️ Could not parse financial result as JSON")
                                    continue
                            
                            # Now result should be a dict
                            if isinstance(result, dict):
                                event_type = result.get('event_type', 'none')
                                
                                if event_type and event_type != 'none':
                                    financial_events['events'].append({
                                        'title': article.get('title', ''),
                                        'event_type': event_type,
                                        'confidence': result.get('confidence', 0.5),
                                        'summary': result.get('summary', '')
                                    })
                    except Exception as e:
                        logger.debug(f"⚠️ Financial analysis skipped: {str(e)[:50]}")
                        continue
                        
                except Exception as e:
                    logger.error(f"❌ Financial classification failed: {e}")
            
            logger.info(f"✅ Financial event classification complete ({len(financial_events['events'])} events found)")
            
            # Save financial analysis results
            financial_file = FINANCIAL_DIR / f"{ticker}_financial.json"
            with open(financial_file, 'w') as f:
                json.dump(financial_events, f, indent=2)
            
            # Step 5: Generate final prediction
            logger.info(f"[5/5] Generating final prediction...")
            
            prediction = self._generate_prediction(
                ticker,
                len(articles),
                sentiment_results,
                financial_events
            )
            
            if prediction:
                # Save prediction
                output_file = OUTPUT_DIR / f"{ticker}_prediction.json"
                with open(output_file, 'w') as f:
                    json.dump(prediction, f, indent=2)
                
                logger.info(f"✅ {ticker}: Prediction saved")
                logger.info(f"   Signal: {prediction.get('prediction', {}).get('final_signal', 'UNKNOWN')}")
                logger.info(f"   Confidence: {prediction.get('prediction', {}).get('confidence_level', 'UNKNOWN')}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error processing {ticker}: {e}", exc_info=True)
            return False
    
    def _generate_prediction(self, ticker, total_articles, sentiment_data, financial_data):
        """Generate final prediction from analysis results"""
        try:
            # Calculate average sentiment
            all_sentiments = (
                sentiment_data.get('general_sentiment', []) + 
                sentiment_data.get('financial_sentiment', [])
            )
            
            if all_sentiments:
                avg_sentiment_score = sum(s.get('score', 0) for s in all_sentiments) / len(all_sentiments)
                positive_count = sum(1 for s in all_sentiments if s.get('sentiment') == 'positive')
                sentiment_label = 'positive' if positive_count > len(all_sentiments) * 0.5 else (
                    'negative' if positive_count < len(all_sentiments) * 0.25 else 'neutral'
                )
            else:
                avg_sentiment_score = 0
                sentiment_label = 'neutral'
            
            # Count event types
            events = financial_data.get('events', [])
            event_counts = {}
            for event in events:
                event_type = event.get('event_type', 'unknown')
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            primary_event = max(event_counts, key=event_counts.get) if event_counts else 'none'
            
            # Generate signal
            final_signal = 'HOLD'
            if sentiment_label == 'positive' and primary_event in [
                'product_launch', 'acquisition', 'partnership', 'earnings_beat', 'revenue_growth'
            ]:
                final_signal = 'BUY'
            elif sentiment_label == 'negative' and primary_event in [
                'bankruptcy', 'layoff', 'lawsuit', 'earnings_miss', 'revenue_decline'
            ]:
                final_signal = 'SELL'
            elif sentiment_label == 'positive':
                final_signal = 'BUY'
            elif sentiment_label == 'negative':
                final_signal = 'SELL'
            
            # Calculate confidence
            confidence = 0.5
            if len(all_sentiments) > 10:
                confidence = 0.85
            elif len(all_sentiments) > 5:
                confidence = 0.75
            elif len(all_sentiments) > 3:
                confidence = 0.65
            
            confidence_level = 'HIGH' if confidence > 0.7 else ('MEDIUM' if confidence > 0.5 else 'LOW')
            
            prediction = {
                'ticker': ticker,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'prediction': {
                    'final_signal': final_signal,
                    'direction': 'UP' if final_signal == 'BUY' else ('DOWN' if final_signal == 'SELL' else 'NEUTRAL'),
                    'combined_score': abs(avg_sentiment_score),
                    'confidence': confidence,
                    'confidence_level': confidence_level,
                    'reasoning': f"Based on {total_articles} articles; Sentiment: {sentiment_label} ({avg_sentiment_score:.2f}); Primary event: {primary_event}; Data sources: {len(all_sentiments)} sentiment analyses, {len(events)} financial events",
                    'components': {
                        'general_sentiment': {
                            'label': sentiment_label,
                            'score': avg_sentiment_score,
                            'weight': 0.4,
                            'contribution': avg_sentiment_score * 0.4
                        },
                        'financial_signal': {
                            'signal': 'POSITIVE' if len(events) > 0 else 'NEUTRAL',
                            'score': len(events) / max(total_articles, 1),
                            'weight': 0.6,
                            'contribution': (len(events) / max(total_articles, 1)) * 0.6
                        }
                    }
                },
                'data_sources': {
                    'total_articles': total_articles,
                    'sentiment_analyses': len(all_sentiments),
                    'financial_events': len(events)
                },
                'generated_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Prediction generation failed: {e}", exc_info=True)
            return None
    
    def run(self):
        """Run the complete pipeline"""
        logger.info("\n" + "="*70)
        logger.info("🚀 STARTING COMPLETE PROCESSING PIPELINE")
        logger.info("="*70)
        
        companies = self.get_companies_from_crawler()
        
        if not companies:
            logger.error("❌ No companies found to process")
            return
        
        successful = 0
        failed = 0
        
        for ticker in companies:
            if self.process_company(ticker):
                successful += 1
            else:
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