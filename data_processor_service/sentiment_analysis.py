# Sentiment analysis using NLP models
"""
Sentiment Analysis for General Company News
Uses transformer models for accurate sentiment detection
"""
import os
import json
import logging
from typing import Dict, List
from datetime import datetime
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment of general company news articles"""
    
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        """
        Initialize sentiment analyzer with FinBERT model
        
        Args:
            model_name: HuggingFace model for financial sentiment
                       Options: "ProsusAI/finbert" (financial focus)
                               "distilbert-base-uncased-finetuned-sst-2-english" (general)
        """
        logger.info(f"Loading sentiment model: {model_name}")
        
        # Use GPU if available
        device = 0 if torch.cuda.is_available() else -1
        
        try:
            # Load model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Create sentiment pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=device,
                truncation=True,
                max_length=512
            )
            
            logger.info(f"✅ Sentiment model loaded successfully (Device: {'GPU' if device == 0 else 'CPU'})")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text
        
        Args:
            text: Article title or content
            
        Returns:
            Dictionary with sentiment label and score
        """
        try:
            # Truncate very long text
            text = text[:2000]
            
            # Get sentiment
            result = self.sentiment_pipeline(text)[0]
            
            # Normalize label
            label = result['label'].lower()
            if label in ['positive', 'pos']:
                label = 'positive'
            elif label in ['negative', 'neg']:
                label = 'negative'
            else:
                label = 'neutral'
            
            return {
                'label': label,
                'score': float(result['score']),
                'confidence': float(result['score'])
            }
        
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {
                'label': 'neutral',
                'score': 0.5,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze sentiment of an entire article
        Combines title and content analysis
        
        Args:
            article: Article dictionary with title and content
            
        Returns:
            Enhanced article with sentiment data
        """
        title = article.get('title', '')
        content = article.get('content', '')
        
        # Analyze title (more impactful)
        title_sentiment = self.analyze_text(title)
        
        # Analyze first 1000 chars of content
        content_preview = content[:1000]
        content_sentiment = self.analyze_text(content_preview)
        
        # Calculate weighted overall sentiment
        # Title has 40% weight, content has 60% weight
        title_weight = 0.4
        content_weight = 0.6
        
        # Convert labels to scores for averaging
        label_to_score = {'positive': 1.0, 'neutral': 0.0, 'negative': -1.0}
        
        title_numeric = label_to_score.get(title_sentiment['label'], 0.0) * title_sentiment['score']
        content_numeric = label_to_score.get(content_sentiment['label'], 0.0) * content_sentiment['score']
        
        overall_score = (title_numeric * title_weight) + (content_numeric * content_weight)
        
        # Determine overall label
        if overall_score > 0.15:
            overall_label = 'positive'
        elif overall_score < -0.15:
            overall_label = 'negative'
        else:
            overall_label = 'neutral'
        
        # Add sentiment data to article
        article['sentiment_analysis'] = {
            'overall': {
                'label': overall_label,
                'score': float(overall_score),
                'confidence': (title_sentiment['confidence'] + content_sentiment['confidence']) / 2
            },
            'title_sentiment': title_sentiment,
            'content_sentiment': content_sentiment,
            'analyzed_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        return article
    
    def analyze_batch(
        self,
        input_dir: str,
        output_dir: str
    ) -> Dict[str, int]:
        """
        Analyze sentiment for all general news articles
        
        Args:
            input_dir: Path to classified_articles/general
            output_dir: Path to sentiment_results
            
        Returns:
            Dictionary with sentiment distribution counts
        """
        os.makedirs(output_dir, exist_ok=True)
        
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        total_articles = 0
        
        logger.info("=" * 70)
        logger.info("SENTIMENT ANALYSIS STARTING")
        logger.info("=" * 70)
        
        # Process each company's general news
        for filename in os.listdir(input_dir):
            if not filename.endswith('_general.json'):
                continue
            
            ticker = filename.replace('_general.json', '')
            input_file = os.path.join(input_dir, filename)
            
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                
                logger.info(f"📊 Analyzing {ticker}: {len(articles)} articles")
                
                analyzed_articles = []
                
                for article in articles:
                    # Analyze sentiment
                    analyzed_article = self.analyze_article(article)
                    analyzed_articles.append(analyzed_article)
                    
                    # Update counts
                    sentiment = analyzed_article['sentiment_analysis']['overall']['label']
                    sentiment_counts[sentiment] += 1
                    total_articles += 1
                
                # Calculate company-level sentiment
                company_sentiments = [
                    a['sentiment_analysis']['overall']['score'] 
                    for a in analyzed_articles
                ]
                avg_sentiment = sum(company_sentiments) / len(company_sentiments) if company_sentiments else 0
                
                # Determine overall company sentiment
                if avg_sentiment > 0.15:
                    company_sentiment = 'positive'
                elif avg_sentiment < -0.15:
                    company_sentiment = 'negative'
                else:
                    company_sentiment = 'neutral'
                
                # Save results
                output_data = {
                    'ticker': ticker,
                    'company_sentiment': {
                        'label': company_sentiment,
                        'average_score': float(avg_sentiment),
                        'article_count': len(analyzed_articles)
                    },
                    'sentiment_distribution': {
                        'positive': sum(1 for a in analyzed_articles 
                                      if a['sentiment_analysis']['overall']['label'] == 'positive'),
                        'neutral': sum(1 for a in analyzed_articles 
                                     if a['sentiment_analysis']['overall']['label'] == 'neutral'),
                        'negative': sum(1 for a in analyzed_articles 
                                      if a['sentiment_analysis']['overall']['label'] == 'negative')
                    },
                    'articles': analyzed_articles,
                    'analyzed_at': datetime.utcnow().isoformat() + 'Z'
                }
                
                output_file = os.path.join(output_dir, f"{ticker}_sentiment.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ {ticker}: {company_sentiment.upper()} "
                          f"(avg: {avg_sentiment:.3f}) - {len(analyzed_articles)} articles")
            
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
        
        logger.info("=" * 70)
        logger.info("SENTIMENT ANALYSIS COMPLETE")
        logger.info(f"Total articles analyzed: {total_articles}")
        logger.info(f"Positive: {sentiment_counts['positive']} "
                   f"({sentiment_counts['positive']/total_articles*100:.1f}%)")
        logger.info(f"Neutral: {sentiment_counts['neutral']} "
                   f"({sentiment_counts['neutral']/total_articles*100:.1f}%)")
        logger.info(f"Negative: {sentiment_counts['negative']} "
                   f"({sentiment_counts['negative']/total_articles*100:.1f}%)")
        logger.info("=" * 70)
        
        return sentiment_counts


def main():
    """Run sentiment analysis on general news"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, "data_processor_service", "classified_articles", "general")
    output_dir = os.path.join(base_dir, "data_processor_service", "sentiment_results")
    
    # Initialize analyzer
    analyzer = SentimentAnalyzer(model_name="ProsusAI/finbert")
    
    # Run analysis
    sentiment_counts = analyzer.analyze_batch(input_dir, output_dir)
    
    print(f"\n✅ Sentiment analysis complete!")
    print(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    main()