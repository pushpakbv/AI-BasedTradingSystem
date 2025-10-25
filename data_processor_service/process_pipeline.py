"""
Enhanced Processing Pipeline with Earnings Analysis & Market Prediction
"""
import os
import sys
import logging
from article_classifier import ArticleClassifier
from sentiment_analysis import SentimentAnalyzer
from financial_analyzer.financial_event_classifier import FinancialEventClassifier
from financial_analyzer.earnings_parser import EarningsParser
from financial_analyzer.market_predictor import MarketImpactPredictor
from financial_analyzer.signal_combiner import SignalCombiner
from ml_pipeline.ml_predictor import MLPredictor  

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_enhanced_pipeline():
    """Execute enhanced processing pipeline with earnings analysis"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Paths
    crawler_data = os.path.join(base_dir, "crawler_service", "data", "by_company")
    classified_dir = os.path.join(base_dir, "data_processor_service", "classified_articles")
    sentiment_dir = os.path.join(base_dir, "data_processor_service", "sentiment_results")
    financial_dir = os.path.join(base_dir, "data_processor_service", "financial_analysis_results")
    earnings_dir = os.path.join(base_dir, "data_processor_service", "earnings_analysis")
    market_impact_dir = os.path.join(base_dir, "data_processor_service", "market_impact_predictions")
    predictions_dir = os.path.join(base_dir, "data_processor_service", "final_predictions")
    
    logger.info("🚀 STARTING ENHANCED PROCESSING PIPELINE")
    logger.info("=" * 70)
    
    # Step 1: Classify articles
    logger.info("STEP 1: Classifying articles...")
    classifier = ArticleClassifier()
    general_count, financial_count = classifier.classify_and_split(
        input_dir=crawler_data,
        output_dir=classified_dir
    )
    logger.info(f"✅ {general_count} general, {financial_count} financial")
    logger.info("=" * 70)
    
    # Step 2: Sentiment analysis
    logger.info("STEP 2: Sentiment analysis on general news...")
    analyzer = SentimentAnalyzer(model_name="ProsusAI/finbert")
    sentiment_counts = analyzer.analyze_batch(
        input_dir=os.path.join(classified_dir, "general"),
        output_dir=sentiment_dir
    )
    logger.info("✅ Sentiment analysis complete")
    logger.info("=" * 70)
    
    # Step 3: Financial event analysis
    logger.info("STEP 3: Financial event classification...")
    financial_analyzer = FinancialEventClassifier()
    financial_results = financial_analyzer.process_batch(
        input_dir=os.path.join(classified_dir, "financial"),
        output_dir=financial_dir
    )
    logger.info("✅ Financial analysis complete")
    logger.info("=" * 70)
    
    # Step 4: ENHANCED - Earnings analysis
    logger.info("STEP 4: Enhanced earnings beat/miss analysis...")
    earnings_parser = EarningsParser()
    earnings_count = process_earnings_analysis(
        financial_dir=financial_dir,
        earnings_dir=earnings_dir,
        parser=earnings_parser
    )
    logger.info(f"✅ Analyzed {earnings_count} earnings reports")
    logger.info("=" * 70)
    
    # Step 5: ENHANCED - Market impact prediction
    logger.info("STEP 5: Market impact prediction...")
    impact_predictor = MarketImpactPredictor()
    impact_count = process_market_predictions(
        earnings_dir=earnings_dir,
        output_dir=market_impact_dir,
        predictor=impact_predictor
    )
    logger.info(f"✅ Generated {impact_count} market predictions")
    logger.info("=" * 70)
    
    # Step 6: Combine all signals
    logger.info("STEP 6: Combining all signals for final predictions...")
    combiner = SignalCombiner(general_weight=0.30, financial_weight=0.70)
    summary = combiner.process_all_companies(
        sentiment_dir=sentiment_dir,
        financial_dir=financial_dir,
        output_dir=predictions_dir
    )
    logger.info("✅ Final predictions generated")
    logger.info("=" * 70)
    
    # Final Summary
    logger.info("📊 ENHANCED PIPELINE COMPLETE")
    logger.info(f"General articles: {general_count}")
    logger.info(f"Financial articles: {financial_count}")
    logger.info(f"Earnings reports analyzed: {earnings_count}")
    logger.info(f"Market predictions: {impact_count}")
    logger.info(f"Companies with predictions: {summary['total_companies']}")
    logger.info("=" * 70)


def process_earnings_analysis(financial_dir: str, earnings_dir: str, parser: EarningsParser) -> int:
    """Process earnings analysis for all financial articles"""
    import json
    os.makedirs(earnings_dir, exist_ok=True)
    
    count = 0
    
    for filename in os.listdir(financial_dir):
        if not filename.endswith('_financial_analysis.json'):
            continue
        
        ticker = filename.replace('_financial_analysis.json', '')
        
        with open(os.path.join(financial_dir, filename), 'r', encoding='utf-8') as f:
                    financial_data = json.load(f)
        
        articles_with_earnings = []
        
        for article in financial_data.get('articles', []):
            # Only process earnings-related articles
            if article.get('financial_analysis', {}).get('event_type') in ['earnings_report', 'earnings_beat', 'earnings_miss']:
                earnings_result = parser.parse_article(article)
                article['earnings_analysis'] = earnings_result
                articles_with_earnings.append(article)
                count += 1
        
        if articles_with_earnings:
            output_file = os.path.join(earnings_dir, f"{ticker}_earnings.json")
            with open(output_file, 'w') as f:
                json.dump({
                    'ticker': ticker,
                    'articles': articles_with_earnings
                }, f, indent=2)
    
    return count


def process_market_predictions(earnings_dir: str, output_dir: str, predictor: MarketImpactPredictor) -> int:
    """Generate market impact predictions"""
    import json
    os.makedirs(output_dir, exist_ok=True)
    
    count = 0
    
    for filename in os.listdir(earnings_dir):
        if not filename.endswith('_earnings.json'):
            continue
        
        with open(os.path.join(earnings_dir, filename), 'r', encoding='utf-8') as f:
            earnings_data = json.load(f)
        
        ticker = earnings_data['ticker']
        articles = earnings_data['articles']
        
        result = predictor.process_company_articles(ticker, articles)
        
        output_file = os.path.join(output_dir, f"{ticker}_market_impact.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        count += 1
    
    return count


if __name__ == "__main__":
    run_enhanced_pipeline()