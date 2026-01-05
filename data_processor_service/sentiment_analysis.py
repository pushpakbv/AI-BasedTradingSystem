import logging
from transformers import pipeline
import torch
import numpy as np

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Sentiment analysis using transformer models"""
    
    def __init__(self):
        logger.info("🚀 Initializing Sentiment Analyzer...")
        
        # Try FinBERT first (financial domain-specific)
        try:
            logger.info("Loading FinBERT model...")
            self.model = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                device=0 if torch.cuda.is_available() else -1,
                truncation=True,
                max_length=512
            )
            self.model_name = "FinBERT"
            logger.info("✅ FinBERT loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ FinBERT failed: {e}, trying distilbert-financial...")
            try:
                self.model = pipeline(
                    "text-classification",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=0 if torch.cuda.is_available() else -1,
                    truncation=True,
                    max_length=512
                )
                self.model_name = "DistilBERT"
                logger.info("✅ DistilBERT loaded successfully")
            except Exception as e2:
                logger.error(f"❌ Failed to load any sentiment model: {e2}")
                self.model = None
                self.model_name = "None"
    
    def analyze(self, text: str):
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            dict with score (-1 to 1) and label
        """
        if not text or not isinstance(text, str):
            return {'score': 0.0, 'label': 'NEUTRAL'}
        
        # Clean text
        text = text.strip()
        if len(text) < 10:
            return {'score': 0.0, 'label': 'NEUTRAL'}
        
        # Truncate to max length (avoid memory issues)
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length]
        
        try:
            if self.model is None:
                logger.warning("Model not loaded, returning neutral")
                return {'score': 0.0, 'label': 'NEUTRAL'}
            
            # Get prediction
            result = self.model(text, truncation=True, max_length=512)
            
            if not result or len(result) == 0:
                return {'score': 0.0, 'label': 'NEUTRAL'}
            
            prediction = result[0]
            label = prediction.get('label', '').upper()
            score = float(prediction.get('score', 0.5))
            
            # Convert label to sentiment score (-1 to 1)
            if 'POSITIVE' in label or label == 'LABEL_1':
                # Positive: convert confidence to 0 to 1
                sentiment_score = score
            elif 'NEGATIVE' in label or label == 'LABEL_0':
                # Negative: convert confidence to -1 to 0
                sentiment_score = -score
            else:
                # Neutral
                sentiment_score = 0.0
            
            # Clamp to -1 to 1
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            logger.debug(f"Sentiment result - Label: {label}, Score: {sentiment_score:.3f}, Confidence: {score:.3f}")
            
            return {
                'score': float(sentiment_score),
                'label': 'POSITIVE' if sentiment_score > 0.1 else 'NEGATIVE' if sentiment_score < -0.1 else 'NEUTRAL',
                'confidence': float(score),
                'model': self.model_name
            }
            
        except Exception as e:
            logger.error(f"❌ Sentiment analysis error: {e}")
            return {'score': 0.0, 'label': 'NEUTRAL', 'error': str(e)}
    
    def get_sentiment(self, text: str):
        """
        Alias for analyze() method - for compatibility
        
        Args:
            text: Text to analyze
            
        Returns:
            dict with score (-1 to 1) and label
        """
        return self.analyze(text)
    
    def predict(self, text: str):
        """
        Alias for analyze() method - for compatibility
        
        Args:
            text: Text to analyze
            
        Returns:
            dict with score (-1 to 1) and label
        """
        return self.analyze(text)
    
    def batch_analyze(self, texts):
        """
        Analyze sentiment for multiple texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            list of {'score': float, 'label': str}
        """
        results = []
        for text in texts:
            try:
                result = self.analyze(text)
                results.append(result)
            except Exception as e:
                logger.warning(f"⚠️ Error analyzing text: {e}")
                results.append({'score': 0.0, 'label': 'NEUTRAL'})
        
        return results
    
    def get_average_sentiment(self, texts):
        """
        Get average sentiment score for multiple texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            float: Average sentiment score (-1 to 1)
        """
        results = self.batch_analyze(texts)
        scores = [r.get('score', 0.0) for r in results]
        
        if not scores:
            return 0.0
        
        avg = float(np.mean(scores))
        return max(-1.0, min(1.0, avg))
    
    def get_sentiment_distribution(self, texts):
        """
        Get distribution of sentiment labels across texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            dict with counts of POSITIVE, NEGATIVE, NEUTRAL
        """
        results = self.batch_analyze(texts)
        
        distribution = {
            'POSITIVE': 0,
            'NEGATIVE': 0,
            'NEUTRAL': 0
        }
        
        for result in results:
            label = result.get('label', 'NEUTRAL')
            if label in distribution:
                distribution[label] += 1
        
        return distribution


def main():
    """Test sentiment analyzer"""
    analyzer = SentimentAnalyzer()
    
    test_texts = [
        "Apple stock surged 15% after beating earnings expectations with strong iPhone sales",
        "Tesla faces production delays and supply chain issues affecting Q4 delivery targets",
        "Microsoft announced a partnership with Samsung for cloud services",
        "Amazon reported disappointing holiday sales and cut workforce by 10,000 employees"
    ]
    
    print("\n" + "="*70)
    print("🧪 Testing Individual Sentiment Analysis")
    print("="*70)
    
    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"\nText: {text[:60]}...")
        print(f"Score: {result['score']:.3f}")
        print(f"Label: {result['label']}")
        print(f"Confidence: {result.get('confidence', 0):.3f}")
    
    print("\n" + "="*70)
    print("📊 Testing Batch Analysis")
    print("="*70)
    
    batch_results = analyzer.batch_analyze(test_texts)
    print(f"\nAnalyzed {len(batch_results)} texts")
    for i, result in enumerate(batch_results, 1):
        print(f"  {i}. Score: {result['score']:.3f}, Label: {result['label']}")
    
    print("\n" + "="*70)
    print("📈 Testing Average Sentiment")
    print("="*70)
    
    avg = analyzer.get_average_sentiment(test_texts)
    print(f"\nAverage sentiment across {len(test_texts)} texts: {avg:.3f}")
    
    print("\n" + "="*70)
    print("📊 Testing Sentiment Distribution")
    print("="*70)
    
    distribution = analyzer.get_sentiment_distribution(test_texts)
    print(f"\nSentiment distribution:")
    for label, count in distribution.items():
        percentage = (count / len(test_texts)) * 100
        print(f"  {label}: {count} ({percentage:.1f}%)")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()