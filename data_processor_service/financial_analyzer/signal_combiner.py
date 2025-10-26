"""
Signal Combiner
Combines general sentiment + financial analysis → Final trading signal
"""
import os
import json
import logging
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalCombiner:
    """Combines multiple signals into final trading recommendation"""
    
    def __init__(
        self,
        general_weight: float = 0.30,
        financial_weight: float = 0.70
    ):
        """
        Initialize combiner with weighting strategy
        
        Args:
            general_weight: Weight for general news sentiment (0-1)
            financial_weight: Weight for financial news signals (0-1)
        """
        self.general_weight = general_weight
        self.financial_weight = financial_weight
        
        # Ensure weights sum to 1
        total = general_weight + financial_weight
        self.general_weight = general_weight / total
        self.financial_weight = financial_weight / total
    
    def normalize_score(self, label: str, score: float) -> float:
        """
        Convert sentiment label + score to normalized -1 to +1 scale
        
        Args:
            label: 'positive', 'neutral', 'negative'
            score: Confidence score
            
        Returns:
            Normalized score (-1 to +1)
        """
        if label == 'positive':
            return score
        elif label == 'negative':
            return -score
        else:  # neutral
            return 0.0
    
    def combine_signals(
        self,
        general_sentiment: Dict,
        financial_analysis: Dict
    ) -> Dict:
        """
        Combine general sentiment and financial signals
        
        Args:
            general_sentiment: Output from sentiment_analysis
            financial_analysis: Output from financial_event_classifier
            
        Returns:
            Combined prediction with trading signal
        """
        # Extract general sentiment score
        gen_label = general_sentiment.get('label', 'neutral')
        gen_score = general_sentiment.get('average_score', 0.0)
        gen_normalized = self.normalize_score(gen_label, abs(gen_score))
        
        # Extract financial signal score
        fin_signal = financial_analysis.get('signal', 'NEUTRAL')
        fin_score = financial_analysis.get('average_score', 0.0)
        
        # Normalize financial score
        if fin_signal == 'POSITIVE':
            fin_normalized = abs(fin_score)
        elif fin_signal == 'NEGATIVE':
            fin_normalized = -abs(fin_score)
        else:
            fin_normalized = 0.0
        
        # Calculate weighted combined score
        combined_score = (
            self.general_weight * gen_normalized +
            self.financial_weight * fin_normalized
        )
        
        # Determine final signal
        if combined_score > 0.30:
            final_signal = 'STRONG_BUY'
            direction = 'UP'
        elif combined_score > 0.10:
            final_signal = 'BUY'
            direction = 'UP'
        elif combined_score < -0.30:
            final_signal = 'STRONG_SELL'
            direction = 'DOWN'
        elif combined_score < -0.10:
            final_signal = 'SELL'
            direction = 'DOWN'
        else:
            final_signal = 'HOLD'
            direction = 'NEUTRAL'
        
        # Calculate confidence
        gen_conf = general_sentiment.get('confidence', 0.5)
        fin_conf = financial_analysis.get('confidence', 0.5)
        avg_confidence = (gen_conf + fin_conf) / 2
        
        if avg_confidence > 0.75:
            confidence_level = 'HIGH'
        elif avg_confidence > 0.50:
            confidence_level = 'MEDIUM'
        else:
            confidence_level = 'LOW'
        
        # Build reasoning
        reasoning_parts = []
        
        if gen_label == 'positive':
            reasoning_parts.append(f"Positive general sentiment ({gen_score:.2f})")
        elif gen_label == 'negative':
            reasoning_parts.append(f"Negative general sentiment ({gen_score:.2f})")
        
        if fin_signal == 'POSITIVE':
            reasoning_parts.append(f"Positive financial signals ({fin_score:.2f})")
        elif fin_signal == 'NEGATIVE':
            reasoning_parts.append(f"Negative financial signals ({fin_score:.2f})")
        
        if financial_analysis.get('event_type'):
            reasoning_parts.append(f"Event: {financial_analysis['event_type']}")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Neutral signals across the board"
        
        return {
            'final_signal': final_signal,
            'direction': direction,
            'combined_score': round(combined_score, 3),
            'confidence': round(avg_confidence, 3),
            'confidence_level': confidence_level,
            'reasoning': reasoning,
            'components': {
                'general_sentiment': {
                    'label': gen_label,
                    'score': round(gen_score, 3),
                    'weight': self.general_weight,
                    'contribution': round(self.general_weight * gen_normalized, 3)
                },
                'financial_signal': {
                    'signal': fin_signal,
                    'score': round(fin_score, 3),
                    'weight': self.financial_weight,
                    'contribution': round(self.financial_weight * fin_normalized, 3)
                }
            }
        }
    
    def process_all_companies(
        self,
        sentiment_dir: str,
        financial_dir: str,
        output_dir: str
    ) -> Dict:
        """
        Generate final predictions for all companies
        
        Args:
            sentiment_dir: Path to sentiment_results
            financial_dir: Path to financial_analysis_results
            output_dir: Path to final_predictions
            
        Returns:
            Summary statistics
        """
        os.makedirs(output_dir, exist_ok=True)
        
        signal_counts = {
            'STRONG_BUY': 0,
            'BUY': 0,
            'HOLD': 0,
            'SELL': 0,
            'STRONG_SELL': 0
        }
        
        logger.info("=" * 70)
        logger.info("COMBINING SIGNALS - FINAL PREDICTIONS")
        logger.info("=" * 70)
        logger.info(f"General sentiment weight: {self.general_weight:.0%}")
        logger.info(f"Financial signal weight: {self.financial_weight:.0%}")
        logger.info("=" * 70)
        
        predictions = []
        
        # Get all companies with sentiment data
        sentiment_files = [f for f in os.listdir(sentiment_dir) if f.endswith('_sentiment.json')]
        
        for sent_file in sentiment_files:
            ticker = sent_file.replace('_sentiment.json', '')
            
            sentiment_path = os.path.join(sentiment_dir, sent_file)
            financial_path = os.path.join(financial_dir, f"{ticker}_financial_analysis.json")
            
            try:
                # Load sentiment data
                with open(sentiment_path, 'r', encoding='utf-8') as f:
                    sentiment_data = json.load(f)
                
                general_sentiment = sentiment_data.get('company_sentiment', {})
                
                # Load financial data (if exists)
                financial_analysis = {'signal': 'NEUTRAL', 'average_score': 0.0, 'confidence': 0.5}
                
                if os.path.exists(financial_path):
                    with open(financial_path, 'r', encoding='utf-8') as f:
                        financial_data = json.load(f)
                    financial_analysis = financial_data.get('financial_outlook', financial_analysis)
                    financial_analysis['event_type'] = list(financial_data.get('event_types', {}).keys())[0] if financial_data.get('event_types') else None
                else:
                    logger.info(f"⚠️  {ticker}: No financial news found, using only general sentiment")
                
                # Combine signals
                prediction = self.combine_signals(general_sentiment, financial_analysis)
                
                # Add metadata
                full_prediction = {
                    'ticker': ticker,
                    'company_name': ticker_to_name.get(ticker, ticker),
                    'date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'prediction': prediction,
                    'data_sources': {
                        'general_articles': sentiment_data.get('company_sentiment', {}).get('article_count', 0),
                        'financial_articles': financial_data.get('financial_outlook', {}).get('article_count', 0) if os.path.exists(financial_path) else 0
                    },
                    'generated_at': datetime.utcnow().isoformat() + 'Z'
                }
                
                predictions.append(full_prediction)
                signal_counts[prediction['final_signal']] += 1
                
                # Save individual prediction
                output_file = os.path.join(output_dir, f"{ticker}_prediction.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(full_prediction, f, indent=2, ensure_ascii=False)
                
                logger.info(f"📊 {ticker}: {prediction['final_signal']} "
                          f"(score: {prediction['combined_score']:.3f}, "
                          f"confidence: {prediction['confidence_level']})")
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
        
        # Save master summary
        summary = {
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'total_companies': len(predictions),
            'signal_distribution': signal_counts,
            'predictions': predictions,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        summary_file = os.path.join(output_dir, 'daily_predictions_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info("=" * 70)
        logger.info("FINAL PREDICTIONS COMPLETE")
        logger.info(f"Total companies analyzed: {len(predictions)}")
        for signal, count in signal_counts.items():
            if count > 0:
                logger.info(f"{signal}: {count}")
        logger.info("=" * 70)
        
        return summary


def main():
    """Generate final predictions"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sentiment_dir = os.path.join(base_dir, "data_processor_service", "sentiment_results")
    financial_dir = os.path.join(base_dir, "data_processor_service", "financial_analysis_results")
    output_dir = os.path.join(base_dir, "data_processor_service", "final_predictions")
    
    combiner = SignalCombiner(
        general_weight=0.30,  # 30% general sentiment
        financial_weight=0.70  # 70% financial signals
    )
    
    summary = combiner.process_all_companies(sentiment_dir, financial_dir, output_dir)
    
    print(f"\n✅ Final predictions generated!")
    print(f"Results: {output_dir}")


if __name__ == "__main__":
    main()