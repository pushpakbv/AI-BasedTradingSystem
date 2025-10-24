"""
Master pipeline: Classification → Sentiment Analysis
Processes crawler output end-to-end
"""
import os
import sys
import logging
from article_classifier import ArticleClassifier
from sentiment_analysis import SentimentAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_full_pipeline():
    """Execute complete processing pipeline"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Paths
    crawler_data = os.path.join(base_dir, "crawler_service", "data", "by_company")
    classified_dir = os.path.join(base_dir, "data_processor_service", "classified_articles")
    sentiment_dir = os.path.join(base_dir, "data_processor_service", "sentiment_results")
    
    logger.info("🚀 STARTING FULL PROCESSING PIPELINE")
    logger.info("=" * 70)
    
    # Step 1: Classify articles
    logger.info("STEP 1: Classifying articles into general/financial...")
    classifier = ArticleClassifier()
    general_count, financial_count = classifier.classify_and_split(
        input_dir=crawler_data,
        output_dir=classified_dir
    )
    
    logger.info(f"✅ Classification complete: {general_count} general, {financial_count} financial")
    logger.info("=" * 70)
    
    # Step 2: Sentiment analysis on general news
    logger.info("STEP 2: Running sentiment analysis on general news...")
    analyzer = SentimentAnalyzer(model_name="ProsusAI/finbert")
    sentiment_counts = analyzer.analyze_batch(
        input_dir=os.path.join(classified_dir, "general"),
        output_dir=sentiment_dir
    )
    
    logger.info("✅ Sentiment analysis complete")
    logger.info("=" * 70)
    
    # Summary
    logger.info("📊 PIPELINE COMPLETE - SUMMARY")
    logger.info(f"Total articles processed: {general_count + financial_count}")
    logger.info(f"General news (sentiment analyzed): {general_count}")
    logger.info(f"Financial news (ready for prediction): {financial_count}")
    logger.info(f"Sentiment breakdown: {sentiment_counts}")
    logger.info("=" * 70)
    
    print(f"\n✅ Pipeline complete!")
    print(f"📁 Classified articles: {classified_dir}")
    print(f"📊 Sentiment results: {sentiment_dir}")


if __name__ == "__main__":
    run_full_pipeline()