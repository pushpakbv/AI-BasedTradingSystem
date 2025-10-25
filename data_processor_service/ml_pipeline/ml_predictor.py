"""
ML Predictor for Production
Uses trained model to predict stock movements from current news
"""
import os
import json
import logging
from typing import Dict, List
from datetime import datetime
import pandas as pd
import numpy as np

from ml_pipeline.model_trainer import StockPredictor
from ml_pipeline.feature_engineer import FeatureEngineer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLPredictor:
    """Production ML predictor for stock movements"""
    
    def __init__(self, model_name: str = 'stock_predictor_xgb'):
        self.predictor = StockPredictor()
        self.predictor.load_model(model_name)
        self.engineer = FeatureEngineer()
        
        logger.info(f"✅ Loaded ML model: {model_name}")
    
    def prepare_prediction_features(
        self,
        ticker: str,
        sentiment_data: Dict,
        financial_data: Dict
    ) -> pd.DataFrame:
        """
        Prepare features for current day prediction
        
        Args:
            ticker: Stock ticker
            sentiment_data: Sentiment analysis results
            financial_data: Financial analysis results
            
        Returns:
            DataFrame with features
        """
        # Create base feature dictionary
        features = {
            'ticker': ticker,
            'has_news': 1 if sentiment_data or financial_data else 0,
            'num_articles': sentiment_data.get('company_sentiment', {}).get('article_count', 0),
            'general_sentiment': sentiment_data.get('company_sentiment', {}).get('average_score', 0.0),
            'financial_signal': self._convert_financial_signal(financial_data),
            'positive_articles': sentiment_data.get('sentiment_distribution', {}).get('positive', 0),
            'negative_articles': sentiment_data.get('sentiment_distribution', {}).get('negative', 0),
        }
        
        # TODO: Fetch current technical indicators (price, RSI, etc.) from market_data_service
        # For now, use dummy values - you'll integrate with your market_data_service
        features.update({
            'Close': 100.0,  # Fetch from market_data_service
            'Volume': 1000000,
            'High': 101.0,
            'Low': 99.0,
            'rsi': 50.0,
            # ... other technical indicators
        })
        
        df = pd.DataFrame([features])
        
        # Engineer features
        df_engineered = self.engineer.create_features(df)
        
        return df_engineered
    
    def _convert_financial_signal(self, financial_data: Dict) -> float:
        """Convert financial signal to numeric score"""
        if not financial_data:
            return 0.0
        
        signal = financial_data.get('financial_outlook', {}).get('signal', 'NEUTRAL')
        
        if signal == 'POSITIVE':
            return 0.5
        elif signal == 'NEGATIVE':
            return -0.5
        else:
            return 0.0
    
    def predict(self, ticker: str, sentiment_data: Dict, financial_data: Dict) -> Dict:
        """
        Make ML-based prediction for a company
        
        Args:
            ticker: Stock ticker
            sentiment_data: Sentiment analysis results
            financial_data: Financial analysis results
            
        Returns:
            Prediction dictionary
        """
        # Prepare features
        df_features = self.prepare_prediction_features(ticker, sentiment_data, financial_data)
        
        # Extract feature values
        X = df_features[self.predictor.feature_names].fillna(0).values
        
        # Predict
        predicted_return = self.predictor.predict(X)[0]
        
        # Determine direction and confidence
        direction = 'UP' if predicted_return > 0 else 'DOWN' if predicted_return < 0 else 'NEUTRAL'
        
        # Convert return to probability-like score
        probability = min(abs(predicted_return) / 5.0, 1.0)  # Assume 5% is max confidence
        
        # Magnitude
        if abs(predicted_return) > 2.0:
            magnitude = 'LARGE'
        elif abs(predicted_return) > 0.5:
            magnitude = 'MEDIUM'
        else:
            magnitude = 'SMALL'
        
        confidence_level = 'HIGH' if probability > 0.7 else 'MEDIUM' if probability > 0.5 else 'LOW'
        
        return {
            'ticker': ticker,
            'predicted_return': float(predicted_return),
            'direction': direction,
            'probability': float(probability),
            'magnitude': magnitude,
            'confidence_level': confidence_level,
            'model_type': self.predictor.model_type,
            'predicted_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    def predict_all_companies(
        self,
        sentiment_dir: str,
        financial_dir: str,
        output_dir: str
    ) -> List[Dict]:
        """
        Generate ML predictions for all companies
        
        Args:
            sentiment_dir: Directory with sentiment results
            financial_dir: Directory with financial analysis
            output_dir: Output directory for predictions
            
        Returns:
            List of prediction results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        
        # Get all sentiment files
        sentiment_files = [f for f in os.listdir(sentiment_dir) if f.endswith('_sentiment.json')]
        
        logger.info(f"Generating ML predictions for {len(sentiment_files)} companies...")
        
        for sent_file in sentiment_files:
            ticker = sent_file.replace('_sentiment.json', '')
            
            try:
                # Load sentiment data
                with open(os.path.join(sentiment_dir, sent_file), 'r', encoding='utf-8') as f:
                    sentiment_data = json.load(f)
                
                # Load financial data (if exists)
                financial_data = {}
                financial_file = os.path.join(financial_dir, f"{ticker}_financial_analysis.json")
                if os.path.exists(financial_file):
                    with open(financial_file, 'r', encoding='utf-8') as f:
                        financial_data = json.load(f)
                
                # Make prediction
                prediction = self.predict(ticker, sentiment_data, financial_data)
                
                # Save individual prediction
                output_file = os.path.join(output_dir, f"{ticker}_ml_prediction.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(prediction, f, indent=2)
                
                results.append(prediction)
                
                logger.info(f"✅ {ticker}: {direction} ({predicted_return:+.2f}%) - {confidence_level} confidence")
                
            except Exception as e:
                logger.error(f"Error predicting {ticker}: {e}")
        
        logger.info(f"✅ ML predictions complete: {len(results)} companies")
        
        return results


def main():
    """Test ML predictor"""
    # Test with sample data
    predictor = MLPredictor('stock_predictor_xgb')
    
    # Sample sentiment data
    sentiment_data = {
        'company_sentiment': {
            'label': 'positive',
            'average_score': 0.35,
            'article_count': 5
        },
        'sentiment_distribution': {
            'positive': 4,
            'neutral': 1,
            'negative': 0
        }
    }
    
    # Sample financial data
    financial_data = {
        'financial_outlook': {
            'signal': 'POSITIVE',
            'average_score': 0.42
        }
    }
    
    # Make prediction
    result = predictor.predict('MSFT', sentiment_data, financial_data)
    
    print("\n" + "=" * 60)
    print("ML PREDICTION TEST")
    print("=" * 60)
    print(f"Ticker: {result['ticker']}")
    print(f"Predicted Return: {result['predicted_return']:+.2f}%")
    print(f"Direction: {result['direction']}")
    print(f"Probability: {result['probability']:.2%}")
    print(f"Confidence: {result['confidence_level']}")
    print("=" * 60)


if __name__ == "__main__":
    main()