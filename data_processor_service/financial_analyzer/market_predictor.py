"""
Market Impact Predictor
Predicts short-term stock movement based on financial news
Uses earnings analysis + historical patterns
"""
import os
import json
import logging
from typing import Dict, List
from datetime import datetime
from .earnings_parser import EarningsParser

logger = logging.getLogger(__name__)


class MarketImpactPredictor:
    """Predicts market impact of financial news"""
    
    def __init__(self):
        self.earnings_parser = EarningsParser()
        
        # Historical impact patterns (simplified - would be ML model in production)
        self.impact_matrix = {
            'BEAT_RAISED': {'direction': 'UP', 'magnitude': 'LARGE', 'probability': 0.85},
            'BEAT_MAINTAINED': {'direction': 'UP', 'magnitude': 'MEDIUM', 'probability': 0.70},
            'BEAT_LOWERED': {'direction': 'NEUTRAL', 'magnitude': 'SMALL', 'probability': 0.55},
            'INLINE_RAISED': {'direction': 'UP', 'magnitude': 'MEDIUM', 'probability': 0.65},
            'INLINE_MAINTAINED': {'direction': 'NEUTRAL', 'magnitude': 'SMALL', 'probability': 0.50},
            'INLINE_LOWERED': {'direction': 'DOWN', 'magnitude': 'MEDIUM', 'probability': 0.65},
            'MISS_RAISED': {'direction': 'NEUTRAL', 'magnitude': 'SMALL', 'probability': 0.50},
            'MISS_MAINTAINED': {'direction': 'DOWN', 'magnitude': 'MEDIUM', 'probability': 0.70},
            'MISS_LOWERED': {'direction': 'DOWN', 'magnitude': 'LARGE', 'probability': 0.85},
        }
        
        # Magnitude ranges (% expected stock movement)
        self.magnitude_ranges = {
            'LARGE': (3.0, 8.0),
            'MEDIUM': (1.5, 3.0),
            'SMALL': (0.5, 1.5),
        }
    
    def predict_impact(self, article: Dict, financial_analysis: Dict) -> Dict:
        """
        Predict market impact of financial article
        
        Args:
            article: Article data
            financial_analysis: Output from earnings_parser
            
        Returns:
            Market impact prediction
        """
        # Get earnings analysis
        if not financial_analysis:
            earnings_result = self.earnings_parser.parse_article(article)
        else:
            earnings_result = financial_analysis
        
        earnings_status = earnings_result.get('earnings_status', 'UNKNOWN')
        guidance_status = earnings_result.get('guidance_status', 'UNKNOWN')
        overall_signal = earnings_result.get('overall_signal', 'NEUTRAL')
        confidence = earnings_result.get('confidence', 0.5)
        
        # Lookup impact pattern
        pattern_key = f"{earnings_status}_{guidance_status}"
        impact = self.impact_matrix.get(pattern_key, {
            'direction': 'NEUTRAL',
            'magnitude': 'SMALL',
            'probability': 0.50
        })
        
        # Get magnitude range
        magnitude = impact['magnitude']
        expected_move = self.magnitude_ranges.get(magnitude, (0.5, 1.5))
        
        # Adjust probability based on confidence
        adjusted_probability = impact['probability'] * confidence
        
        # Build prediction
        prediction = {
            'direction': impact['direction'],  # UP, DOWN, NEUTRAL
            'probability': round(adjusted_probability, 3),
            'expected_change_min': expected_move[0],
            'expected_change_max': expected_move[1],
            'magnitude': magnitude,  # LARGE, MEDIUM, SMALL
            'timeframe': 'next_trading_day',
            'confidence_level': self._get_confidence_level(adjusted_probability),
            'drivers': self._identify_drivers(earnings_result),
            'risk_factors': self._identify_risks(earnings_result, article),
            'predicted_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        return prediction
    
    def _get_confidence_level(self, probability: float) -> str:
        """Convert probability to confidence level"""
        if probability >= 0.75:
            return 'HIGH'
        elif probability >= 0.60:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _identify_drivers(self, earnings_result: Dict) -> List[str]:
        """Identify key drivers of the prediction"""
        drivers = []
        
        earnings_status = earnings_result.get('earnings_status')
        guidance_status = earnings_result.get('guidance_status')
        financial_data = earnings_result.get('financial_data', {})
        
        if earnings_status == 'BEAT':
            drivers.append('Earnings beat estimates')
        elif earnings_status == 'MISS':
            drivers.append('Earnings missed estimates')
        
        if guidance_status == 'RAISED':
            drivers.append('Raised guidance')
        elif guidance_status == 'LOWERED':
            drivers.append('Lowered guidance')
        
        if financial_data.get('eps_beat_percent'):
            beat_pct = financial_data['eps_beat_percent']
            if abs(beat_pct) > 5:
                drivers.append(f'EPS beat by {beat_pct:.1f}%')
        
        if financial_data.get('growth_rates'):
            high_growth = [g for g in financial_data['growth_rates'] if g > 20]
            if high_growth:
                drivers.append(f'Strong growth rates: {max(high_growth):.1f}%')
        
        return drivers if drivers else ['Mixed signals']
    
    def _identify_risks(self, earnings_result: Dict, article: Dict) -> List[str]:
        """Identify risk factors"""
        risks = []
        
        confidence = earnings_result.get('confidence', 0.5)
        
        if confidence < 0.6:
            risks.append('Low confidence in analysis')
        
        earnings_status = earnings_result.get('earnings_status')
        guidance_status = earnings_result.get('guidance_status')
        
        if earnings_status == 'UNKNOWN' or guidance_status == 'UNKNOWN':
            risks.append('Unclear earnings or guidance data')
        
        # Check for mixed signals
        if (earnings_status == 'BEAT' and guidance_status == 'LOWERED') or \
           (earnings_status == 'MISS' and guidance_status == 'RAISED'):
            risks.append('Mixed signals (earnings vs guidance)')
        
        # Check content length (shorter = less info)
        content = article.get('content', '')
        if len(content.split()) < 200:
            risks.append('Limited article content')
        
        return risks if risks else ['Standard market volatility']
    
    def process_company_articles(
        self,
        ticker: str,
        financial_articles: List[Dict]
    ) -> Dict:
        """
        Process all financial articles for a company
        
        Args:
            ticker: Company ticker
            financial_articles: List of financial articles
            
        Returns:
            Aggregated market impact prediction
        """
        predictions = []
        
        for article in financial_articles:
            # Parse earnings if not already done
            if 'earnings_analysis' not in article:
                earnings_analysis = self.earnings_parser.parse_article(article)
                article['earnings_analysis'] = earnings_analysis
            else:
                earnings_analysis = article['earnings_analysis']
            
            # Predict impact
            impact = self.predict_impact(article, earnings_analysis)
            
            predictions.append({
                'article_url': article.get('url'),
                'article_title': article.get('title'),
                'earnings_analysis': earnings_analysis,
                'market_impact': impact
            })
        
        # Aggregate predictions
        aggregated = self._aggregate_predictions(predictions)
        
        return {
            'ticker': ticker,
            'article_count': len(predictions),
            'individual_predictions': predictions,
            'aggregated_prediction': aggregated,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _aggregate_predictions(self, predictions: List[Dict]) -> Dict:
        """Aggregate multiple predictions into one"""
        if not predictions:
            return {
                'direction': 'NEUTRAL',
                'probability': 0.5,
                'confidence_level': 'LOW'
            }
        
        # Count directions
        up_count = sum(1 for p in predictions if p['market_impact']['direction'] == 'UP')
        down_count = sum(1 for p in predictions if p['market_impact']['direction'] == 'DOWN')
        neutral_count = len(predictions) - up_count - down_count
        
        # Average probability
        avg_probability = sum(p['market_impact']['probability'] for p in predictions) / len(predictions)
        
        # Determine direction
        if up_count > down_count and up_count > neutral_count:
            direction = 'UP'
        elif down_count > up_count and down_count > neutral_count:
            direction = 'DOWN'
        else:
            direction = 'NEUTRAL'
        
        # Get strongest magnitude
        magnitudes = [p['market_impact']['magnitude'] for p in predictions]
        magnitude_priority = {'LARGE': 3, 'MEDIUM': 2, 'SMALL': 1}
        strongest_magnitude = max(magnitudes, key=lambda m: magnitude_priority.get(m, 0))
        
        return {
            'direction': direction,
            'probability': round(avg_probability, 3),
            'magnitude': strongest_magnitude,
            'confidence_level': self._get_confidence_level(avg_probability),
            'signal_distribution': {
                'up': up_count,
                'down': down_count,
                'neutral': neutral_count
            }
        }


def main():
    """Test market impact predictor"""
    predictor = MarketImpactPredictor()
    
    test_article = {
        'title': 'Amazon beats Q3 earnings with strong AWS growth',
        'content': '''Amazon.com Inc reported third-quarter earnings that beat analyst 
        estimates, with revenue of $143.1 billion versus expected $141.5 billion. 
        EPS was $0.94, above the expected $0.58. The company raised full-year guidance 
        citing strong AWS cloud growth of 19% year-over-year. Operating income increased 
        55% to $11.2 billion.'''
    }
    
    result = predictor.predict_impact(test_article, None)
    
    print("=" * 60)
    print("MARKET IMPACT PREDICTION")
    print("=" * 60)
    print(f"Direction: {result['direction']}")
    print(f"Probability: {result['probability']:.1%}")
    print(f"Expected Change: {result['expected_change_min']:.1f}% to {result['expected_change_max']:.1f}%")
    print(f"Magnitude: {result['magnitude']}")
    print(f"Confidence: {result['confidence_level']}")
    print(f"\nDrivers:")
    for driver in result['drivers']:
        print(f"  - {driver}")
    print(f"\nRisks:")
    for risk in result['risk_factors']:
        print(f"  - {risk}")


if __name__ == "__main__":
    main()