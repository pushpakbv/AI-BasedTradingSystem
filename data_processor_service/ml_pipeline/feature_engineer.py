"""
Feature Engineering Pipeline
Creates ML-ready features from raw data
"""
import pandas as pd
import numpy as np
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Advanced feature engineering for stock prediction"""
    
    def __init__(self):
        self.feature_names = []
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create all ML features
        
        Args:
            df: DataFrame with raw data
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Creating ML features...")
        
        df = df.copy()
        
        # 1. Price momentum features
        df = self._add_momentum_features(df)
        
        # 2. Volatility features
        df = self._add_volatility_features(df)
        
        # 3. Volume features
        df = self._add_volume_features(df)
        
        # 4. News-based features
        df = self._add_news_features(df)
        
        # 5. Calendar features
        df = self._add_calendar_features(df)
        
        # 6. Interaction features
        df = self._add_interaction_features(df)
        
        # Store feature names
        self.feature_names = [col for col in df.columns if col not in [
            'ticker', 'next_day_return', 'next_day_direction'
        ]]
        
        logger.info(f"✅ Created {len(self.feature_names)} features")
        return df
    
    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Price momentum indicators"""
        # Multiple timeframe returns
        for days in [1, 2, 3, 5, 10, 20]:
            df[f'return_{days}d'] = df.groupby('ticker')['Close'].pct_change(days) * 100
        
        # Moving average crossovers
        df['sma5_sma20_cross'] = (df['sma_5'] / df['sma_20'] - 1) * 100
        df['sma20_sma50_cross'] = (df['sma_20'] / df['sma_50'] - 1) * 100
        
        # Price momentum (Rate of Change)
        df['roc_5'] = ((df['Close'] / df['Close'].shift(5)) - 1) * 100
        df['roc_20'] = ((df['Close'] / df['Close'].shift(20)) - 1) * 100
        
        return df
    
    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Volatility indicators"""
        # Historical volatility (multiple windows)
        for window in [5, 10, 20]:
            df[f'volatility_{window}d'] = df.groupby('ticker')['return_1d'].rolling(window).std().reset_index(0, drop=True)
        
        # Volatility ratio
        df['vol_ratio_5_20'] = df['volatility_5d'] / df['volatility_20d']
        
        # High-Low range
        df['high_low_pct'] = ((df['High'] - df['Low']) / df['Close']) * 100
        
        # Average True Range (ATR)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(14).mean()
        
        return df
    
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Volume-based features"""
        # Volume moving averages
        df['volume_sma5'] = df.groupby('ticker')['Volume'].rolling(5).mean().reset_index(0, drop=True)
        df['volume_sma20'] = df.groupby('ticker')['Volume'].rolling(20).mean().reset_index(0, drop=True)
        
        # Volume ratio
        df['volume_ratio_5'] = df['Volume'] / df['volume_sma5']
        df['volume_ratio_20'] = df['Volume'] / df['volume_sma20']
        
        # On-Balance Volume (OBV)
        df['obv'] = (np.sign(df['Close'].diff()) * df['Volume']).cumsum()
        df['obv_sma5'] = df.groupby('ticker')['obv'].rolling(5).mean().reset_index(0, drop=True)
        
        return df
    
    def _add_news_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """News-based features"""
        # Cumulative news sentiment (last 5 days)
        df['sentiment_5d_avg'] = df.groupby('ticker')['general_sentiment'].rolling(5, min_periods=1).mean().reset_index(0, drop=True)
        df['sentiment_5d_sum'] = df.groupby('ticker')['general_sentiment'].rolling(5, min_periods=1).sum().reset_index(0, drop=True)
        
        # Financial signal momentum
        df['financial_signal_5d_avg'] = df.groupby('ticker')['financial_signal'].rolling(5, min_periods=1).mean().reset_index(0, drop=True)
        
        # News frequency (articles per day)
        df['news_frequency_5d'] = df.groupby('ticker')['num_articles'].rolling(5, min_periods=1).sum().reset_index(0, drop=True)
        
        # Positive/negative article ratio
        df['pos_neg_ratio'] = df['positive_articles'] / (df['negative_articles'] + 1)
        
        # Days since last news
        df['days_since_news'] = (~df['has_news'].astype(bool)).groupby(df['ticker']).cumsum()
        df.loc[df['has_news'] == 1, 'days_since_news'] = 0
        
        return df
    
    def _add_calendar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calendar/temporal features"""
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        # Beginning/end of month
        df['is_month_start'] = (df.index.day <= 5).astype(int)
        df['is_month_end'] = (df.index.day >= 25).astype(int)
        
        # Market regime (bull/bear based on 50-day MA)
        df['market_regime'] = (df['Close'] > df['sma_50']).astype(int)
        
        return df
    
    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Interaction between news and price features"""
        # Sentiment * Momentum
        df['sentiment_momentum'] = df['general_sentiment'] * df['return_5d']
        
        # Financial signal * Volatility
        df['financial_volatility'] = df['financial_signal'] * df['volatility_20d']
        
        # News volume * Price change
        df['news_volume_return'] = df['num_articles'] * df['return_1d']
        
        # RSI * Sentiment
        df['rsi_sentiment'] = df['rsi'] * df['general_sentiment']
        
        return df
    
    def get_feature_importance_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for model training
        
        Returns:
            X (features), y (target)
        """
        # Select feature columns
        X = df[self.feature_names].fillna(0)
        
        # Target: next day return
        y = df['next_day_return'].fillna(0)
        
        return X.values, y.values
    
    def get_classification_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for classification (UP/DOWN prediction)
        
        Returns:
            X (features), y (target: 0=DOWN, 1=UP)
        """
        X = df[self.feature_names].fillna(0)
        y = df['next_day_direction'].fillna(0)
        
        return X.values, y.values


def main():
    """Test feature engineering"""
    import sys
    sys.path.append('..')
    
    from ml_pipeline.historical_data_collector import HistoricalDataCollector
    
    # Load sample data
    collector = HistoricalDataCollector()
    data_file = os.path.join(collector.data_dir, 'training_dataset.csv')
    
    if not os.path.exists(data_file):
        print("Training dataset not found. Run historical_data_collector.py first.")
        return
    
    df = pd.read_csv(data_file, index_col=0, parse_dates=True)
    
    # Engineer features
    engineer = FeatureEngineer()
    df_features = engineer.create_features(df)
    
    print("=" * 70)
    print("FEATURE ENGINEERING COMPLETE")
    print("=" * 70)
    print(f"Total features: {len(engineer.feature_names)}")
    print(f"\nFeature categories:")
    print(f"  - Momentum: {len([f for f in engineer.feature_names if 'return' in f or 'roc' in f])}")
    print(f"  - Volatility: {len([f for f in engineer.feature_names if 'volatility' in f or 'atr' in f])}")
    print(f"  - Volume: {len([f for f in engineer.feature_names if 'volume' in f or 'obv' in f])}")
    print(f"  - News: {len([f for f in engineer.feature_names if 'sentiment' in f or 'financial' in f or 'news' in f])}")
    print(f"  - Calendar: {len([f for f in engineer.feature_names if 'day' in f or 'month' in f or 'quarter' in f])}")
    
    # Show sample
    print(f"\nSample features:")
    print(df_features[engineer.feature_names[:10]].head())


if __name__ == "__main__":
    import os
    main()