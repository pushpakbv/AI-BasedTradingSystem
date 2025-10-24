"""
Financial Event Classifier
Categorizes financial articles and extracts market signals
"""
import os
import json
import logging
import re
from typing import Dict, List, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialEventClassifier:
    """Classifies financial news into actionable event types"""
    
    def __init__(self):
        # Event type patterns
        self.event_patterns = {
            'earnings_report': {
                'keywords': ['earnings', 'quarterly results', 'q1', 'q2', 'q3', 'q4', 
                           'fiscal quarter', 'eps', 'revenue report'],
                'weight': 10
            },
            'earnings_beat': {
                'keywords': ['beat', 'topped', 'exceeded', 'surpassed', 'above estimates',
                           'better than expected'],
                'weight': 8
            },
            'earnings_miss': {
                'keywords': ['miss', 'fell short', 'below estimates', 'disappointed',
                           'worse than expected', 'lower than forecast'],
                'weight': 8
            },
            'guidance_raised': {
                'keywords': ['raised guidance', 'increased outlook', 'upgraded forecast',
                           'boosted expectations', 'raised forecast'],
                'weight': 9
            },
            'guidance_lowered': {
                'keywords': ['lowered guidance', 'reduced outlook', 'cut forecast',
                           'downgraded expectations', 'trimmed guidance'],
                'weight': 9
            },
            'analyst_upgrade': {
                'keywords': ['upgrade', 'raised price target', 'increased rating',
                           'rated outperform', 'raised to buy'],
                'weight': 7
            },
            'analyst_downgrade': {
                'keywords': ['downgrade', 'lowered price target', 'reduced rating',
                           'rated underperform', 'cut to sell'],
                'weight': 7
            },
            'merger_acquisition': {
                'keywords': ['merger', 'acquisition', 'acquires', 'merges with',
                           'takeover', 'buys', 'deal'],
                'weight': 6
            },
            'dividend_buyback': {
                'keywords': ['dividend', 'share buyback', 'stock repurchase',
                           'return to shareholders'],
                'weight': 5
            }
        }
        
        # Positive/negative signal keywords
        self.positive_signals = {
            'strong', 'growth', 'increase', 'rising', 'improved', 'solid',
            'robust', 'accelerating', 'outperform', 'momentum', 'optimistic',
            'beat', 'exceeded', 'raised', 'upgrade', 'buy', 'bullish'
        }
        
        self.negative_signals = {
            'weak', 'decline', 'decrease', 'falling', 'deteriorating', 'concerns',
            'challenging', 'slowdown', 'underperform', 'headwinds', 'cautious',
            'miss', 'below', 'lowered', 'downgrade', 'sell', 'bearish'
        }
    
    def classify_event(self, article: Dict) -> Dict:
        """
        Classify financial article into event types
        
        Args:
            article: Article dictionary with title and content
            
        Returns:
            Dictionary with event classification and signals
        """
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        full_text = f"{title} {title} {content}"  # Weight title 2x
        
        # Detect event types
        detected_events = []
        max_weight = 0
        primary_event = None
        
        for event_type, config in self.event_patterns.items():
            keywords = config['keywords']
            weight = config['weight']
            
            matches = sum(1 for keyword in keywords if keyword in full_text)
            
            if matches > 0:
                score = matches * weight
                detected_events.append({
                    'type': event_type,
                    'matches': matches,
                    'score': score
                })
                
                if score > max_weight:
                    max_weight = score
                    primary_event = event_type
        
        # Calculate signal strength
        positive_count = sum(1 for signal in self.positive_signals if signal in full_text)
        negative_count = sum(1 for signal in self.negative_signals if signal in full_text)
        
        # Determine market signal
        if primary_event in ['earnings_beat', 'guidance_raised', 'analyst_upgrade']:
            market_signal = 'POSITIVE'
        elif primary_event in ['earnings_miss', 'guidance_lowered', 'analyst_downgrade']:
            market_signal = 'NEGATIVE'
        elif positive_count > negative_count * 1.5:
            market_signal = 'POSITIVE'
        elif negative_count > positive_count * 1.5:
            market_signal = 'NEGATIVE'
        else:
            market_signal = 'NEUTRAL'
        
        # Calculate confidence
        total_signals = positive_count + negative_count
        confidence = min(1.0, (max_weight / 50.0) + (total_signals / 20.0))
        
        return {
            'primary_event': primary_event or 'general_financial',
            'all_events': detected_events,
            'market_signal': market_signal,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count,
            'confidence': round(confidence, 3)
        }
    
    def extract_numbers(self, text: str) -> Dict:
        """Extract financial numbers from text"""
        numbers = {
            'revenue': None,
            'eps': None,
            'profit': None,
            'percentages': []
        }
        
        # Revenue patterns
        revenue_pattern = r'\$(\d+\.?\d*)\s*(billion|million|B|M)'
        revenue_matches = re.findall(revenue_pattern, text, re.IGNORECASE)
        if revenue_matches:
            value, unit = revenue_matches[0]
            multiplier = 1e9 if unit.lower() in ['billion', 'b'] else 1e6
            numbers['revenue'] = float(value) * multiplier
        
        # EPS patterns
        eps_pattern = r'eps[:\s]+\$?(\d+\.?\d*)'
        eps_matches = re.findall(eps_pattern, text, re.IGNORECASE)
        if eps_matches:
            numbers['eps'] = float(eps_matches[0])
        
        # Percentage patterns
        pct_pattern = r'(\d+\.?\d*)%'
        pct_matches = re.findall(pct_pattern, text)
        numbers['percentages'] = [float(p) for p in pct_matches]
        
        return numbers
    
    def analyze_financial_article(self, article: Dict) -> Dict:
        """
        Complete financial analysis of an article
        
        Args:
            article: Article dictionary
            
        Returns:
            Enhanced article with financial analysis
        """
        title = article.get('title', '')
        content = article.get('content', '')
        
        # Classify event
        event_data = self.classify_event(article)
        
        # Extract numbers
        numbers = self.extract_numbers(f"{title} {content}")
        
        # Add financial analysis to article
        article['financial_analysis'] = {
            'event_type': event_data['primary_event'],
            'market_signal': event_data['market_signal'],
            'confidence': event_data['confidence'],
            'detected_events': event_data['all_events'],
            'indicators': {
                'positive': event_data['positive_indicators'],
                'negative': event_data['negative_indicators']
            },
            'extracted_numbers': numbers,
            'analyzed_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        return article
    
    def process_batch(self, input_dir: str, output_dir: str) -> Dict:
        """
        Process all financial news articles
        
        Args:
            input_dir: Path to classified_articles/financial
            output_dir: Path to financial_analysis_results
            
        Returns:
            Summary statistics
        """
        os.makedirs(output_dir, exist_ok=True)
        
        signal_counts = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
        event_counts = {}
        total_articles = 0
        
        logger.info("=" * 70)
        logger.info("FINANCIAL EVENT ANALYSIS STARTING")
        logger.info("=" * 70)
        
        for filename in os.listdir(input_dir):
            if not filename.endswith('_financial.json'):
                continue
            
            ticker = filename.replace('_financial.json', '')
            input_file = os.path.join(input_dir, filename)
            
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                
                logger.info(f"💰 Analyzing {ticker}: {len(articles)} financial articles")
                
                analyzed_articles = []
                
                for article in articles:
                    analyzed = self.analyze_financial_article(article)
                    analyzed_articles.append(analyzed)
                    
                    # Update counts
                    signal = analyzed['financial_analysis']['market_signal']
                    signal_counts[signal] += 1
                    
                    event_type = analyzed['financial_analysis']['event_type']
                    event_counts[event_type] = event_counts.get(event_type, 0) + 1
                    
                    total_articles += 1
                
                # Calculate company-level financial signal
                company_signals = []
                for a in analyzed_articles:
                    sig = a['financial_analysis']['market_signal']
                    conf = a['financial_analysis']['confidence']
                    
                    if sig == 'POSITIVE':
                        company_signals.append(conf)
                    elif sig == 'NEGATIVE':
                        company_signals.append(-conf)
                    else:
                        company_signals.append(0)
                
                avg_signal = sum(company_signals) / len(company_signals) if company_signals else 0
                
                if avg_signal > 0.2:
                    company_financial_outlook = 'POSITIVE'
                elif avg_signal < -0.2:
                    company_financial_outlook = 'NEGATIVE'
                else:
                    company_financial_outlook = 'NEUTRAL'
                
                # Save results
                output_data = {
                    'ticker': ticker,
                    'financial_outlook': {
                        'signal': company_financial_outlook,
                        'average_score': round(avg_signal, 3),
                        'article_count': len(analyzed_articles)
                    },
                    'signal_distribution': {
                        'positive': sum(1 for a in analyzed_articles 
                                      if a['financial_analysis']['market_signal'] == 'POSITIVE'),
                        'neutral': sum(1 for a in analyzed_articles 
                                     if a['financial_analysis']['market_signal'] == 'NEUTRAL'),
                        'negative': sum(1 for a in analyzed_articles 
                                      if a['financial_analysis']['market_signal'] == 'NEGATIVE')
                    },
                    'event_types': {},
                    'articles': analyzed_articles,
                    'analyzed_at': datetime.utcnow().isoformat() + 'Z'
                }
                
                # Count event types for this company
                for article in analyzed_articles:
                    event = article['financial_analysis']['event_type']
                    output_data['event_types'][event] = output_data['event_types'].get(event, 0) + 1
                
                output_file = os.path.join(output_dir, f"{ticker}_financial_analysis.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ {ticker}: {company_financial_outlook} outlook "
                          f"(score: {avg_signal:.3f}) - {len(analyzed_articles)} articles")
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
        
        logger.info("=" * 70)
        logger.info("FINANCIAL ANALYSIS COMPLETE")
        logger.info(f"Total articles: {total_articles}")
        logger.info(f"Positive signals: {signal_counts['POSITIVE']} "
                   f"({signal_counts['POSITIVE']/total_articles*100:.1f}%)")
        logger.info(f"Neutral signals: {signal_counts['NEUTRAL']} "
                   f"({signal_counts['NEUTRAL']/total_articles*100:.1f}%)")
        logger.info(f"Negative signals: {signal_counts['NEGATIVE']} "
                   f"({signal_counts['NEGATIVE']/total_articles*100:.1f}%)")
        logger.info("=" * 70)
        logger.info("Event Type Distribution:")
        for event, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {event}: {count}")
        logger.info("=" * 70)
        
        return {
            'signal_counts': signal_counts,
            'event_counts': event_counts,
            'total_articles': total_articles
        }


def main():
    """Run financial event analysis"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_dir = os.path.join(base_dir, "data_processor_service", "classified_articles", "financial")
    output_dir = os.path.join(base_dir, "data_processor_service", "financial_analysis_results")
    
    analyzer = FinancialEventClassifier()
    results = analyzer.process_batch(input_dir, output_dir)
    
    print(f"\n✅ Financial analysis complete!")
    print(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    main()